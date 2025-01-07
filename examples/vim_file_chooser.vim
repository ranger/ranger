" Compatible with ranger 1.4.2 through 1.7.*
"
" Add ranger as a file chooser in (Neo)Vim.
"
" You need to either
"
" - copy the content of this file to your ~/.vimrc resp. ~/.config/nvim/init.vim,
" - or put it into ~/.vim/plugin respectively ~/.config/nvim/plugin,
" - or source this file directly:
"
"     let s:fp = "/path/to/vim_file_chooser.vim"
"     if filereadable(s:fp) | exec "source" s:fp | endif
"     unlet s:fp
"
" If you add this code to the .vimrc, ranger can be started using the command
" ":RangerChooser" or the keybinding "-".  Once you select one or more
" files, press enter and ranger will quit again and vim will open the selected
" files.

if &compatible || exists('g:loaded_rangerchooser')
    finish
endif
let g:loaded_rangerchooser = 1

let s:temp = tempname()
if executable('ranger')
  " The option --choosefiles was added in ranger 1.5.1.
  " Use --choosefile with ranger 1.4.2 through 1.5.0 instead.
  command! -nargs=? -bar -complete=dir RangerChooser call RangerChooser('ranger', '--choosefiles='..s:temp, '--selectfile', <q-args>)
elseif executable('lf')
  command! -nargs=? -bar -complete=dir RangerChooser call RangerChooser('lf', '-selection-path', s:temp, <q-args>)
elseif executable('yazi')
  command! -nargs=? -bar -complete=dir RangerChooser call RangerChooser('yazi', '--chooser-file='..s:temp, <q-args>)
elseif executable('nnn')
  command! -nargs=? -bar -complete=dir RangerChooser call RangerChooser('nnn', '-p', s:temp, <q-args>)
endif

if exists(':RangerChooser') != 2
  " Fallback to built-in Netrw if none of Ranger/LF/Yazi/NNN is available.
  command! -nargs=? -bar -complete=dir RangerChooser call <sid>Opendir(<q-args>)
  function! s:Opendir(dir) abort
    let path = a:dir
    if empty(path)
      let path = expand('%')
      if path =~# '^$\|^term:[\/][\/]'
        execute 'edit' '.'
      else
        " fix for - to select the current file,
        " see https://github.com/tpope/vim-vinegar/issues/136
        let save_dir = chdir(expand('%:p:h'))

        try
        execute 'edit' '%:h'
        let pattern = '^\%(| \)*'.escape(expand('#:t'), '.*[]~\').'[/*|@=]\=\%($\|\s\)'
        call search(pattern, 'wc')

        finally | call chdir(save_dir) | endtry
      endif
    else
      execute 'edit' path
    endif
  endfunction
else
  function! RangerChooser(...)
    let path = a:000[-1]
    if empty(path)
      let path = expand('%')
      if filereadable(path)
        let uses_term = has('nvim') || has('gui_running')
        if !uses_term | let path = shellescape(path,1) | endif
      else
        let path = '.'
      endif
    endif
    let cmd = a:000[:-2] + [path]
    call s:term(cmd)
  endfunction

  if has('nvim')
    function! s:term(cmd) abort
      enew
      call termopen(a:cmd, { 'on_exit': function('s:open') })
    endfunction
  else
    if has('gui_running')
      if has('terminal')
        function! s:term(cmd) abort
          call term_start(a:cmd, {'exit_cb': function('s:term_close'), 'curwin': 1})
        endfunction

        function! s:term_close(job_id, event) abort
          if a:event == 'exit'
            bwipeout!
            call s:open()
          endif
        endfunction
      else
        function! s:term(dummy) abort
          echomsg 'GUI is running but terminal is not supported.'
        endfunction
      endif
    else
      function! s:term(cmd) abort
        exec 'silent !'..join(a:cmd) | call s:open()
      endfunction
    endif
  endif

  function! s:open(...)
    if !filereadable(s:temp)
      " if &buftype ==# 'terminal'
      "   bwipeout!
      " endif
      redraw!
      " Nothing to read.
      return
    endif
    let names = readfile(s:temp)
    if empty(names)
      redraw!
      " Nothing to open.
      return
    endif
    " Edit the first item.
    exec 'edit' fnameescape(names[0])
    " Add any remaning items to the arg list/buffer list.
    for name in names[1:]
      exec 'argadd' fnameescape(name)
    endfor
    redraw!
  endfunction
endif

nnoremap <silent> <plug>(RangerChooser) :<c-u>RangerChooser<CR>

if exists("g:no_plugin_maps") || exists("g:no_rangerchooser_maps") | finish | endif

if !hasmapto('<plug>(RangerChooser)', 'n')
  nmap <silent> - <plug>(RangerChooser)
endif
