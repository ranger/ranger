" To add Ranger as a file chooser in (Neo)Vim, go to 
" https://github.com/Konfekt/filepicker.vim/blob/main/plugin/filepicker.vim
" and either
"
" - copy the content of this file to your ~/.vimrc resp. ~/.config/nvim/init.vim,
" - or put it into ~/.vim/plugin respectively ~/.config/nvim/plugin,
" - or source this file directly:
"
"     let s:fp = "/path/to/filepicker.vim"
"     if filereadable(s:fp) | exec "source" s:fp | endif
"     unlet s:fp
"
" If you add this code to the .vimrc, ranger can be started using the command
" ":FilePicker" or the keybinding "-".  Once you select one or more
" files, press enter and ranger will quit again and vim will open the selected
" files.

command! -nargs=? -bar -complete=dir RangerChooser echomsg ":RangerChooser has been deprecated in favor of :FilePicker available at https://github.com/Konfekt/filepicker.vim"
