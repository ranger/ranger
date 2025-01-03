" Compatible with ranger 1.4.2 through 1.7.*
"
" Add ranger as a file chooser in vim.
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
" ":RangerChooser" or the keybinding "<leader>r".  Once you select one or more
" files, press enter and ranger will quit again and vim will open the selected
" files.

let s:temp = tempname()
if executable('ranger')
  " The option --choosefiles was added in ranger 1.5.1.
  " Use --choosefile with ranger 1.4.2 through 1.5.0 instead.
  command! -nargs=? -bar -complete=dir RangerChooser call RangerChooser('ranger', '--choosefiles='..s:temp, '--selectfile', <q-args>)
elseif executable('lf')
  command! -nargs=? -bar -complete=dir RangerChooser call RangerChooser('lf', '-selection-path', s:temp, <q-args>)
elseif executable('nnn')
  command! -nargs=? -bar -complete=dir RangerChooser call RangerChooser('nnn', '-p', s:temp, <q-args>)
endif

nnoremap <leader>r :<C-U>RangerChooser<CR>

if exists(':RangerChooser') == 2
  function! RangerChooser(...)
    let path = a:000[-1]
    let cmd = a:000[:-2] + (empty(path) ?
          \ [filereadable(expand('%')) ? expand('%:p') : '.'] : [path])
    if has('nvim')
      enew
      call termopen(cmd, { 'on_exit': function('s:open') })
    else
      if has('gui_running')
        if has('terminal')
          call term_start(cmd, {'exit_cb': function('s:term_close'), 'curwin': 1})
        else
          echomsg 'GUI is running but terminal is not supported.'
        endif
      else
        exec 'silent !'..join(cmd) | call s:open()
      endif
    endif
  endfunction

  if has('gui_running') && has('terminal')
    function! s:term_close(job_id, event)
      if a:event == 'exit'
        bwipeout!
        call s:open()
      endif
    endfunction
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
