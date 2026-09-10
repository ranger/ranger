from .browsercolumn import BrowserColumn

class BrowserColumnTree(BrowserColumn):
    def __init__(self, win, level, tab=None):
        """Initializes a Browser Column Widget that 
        displays directories in a tree
        """
        BrowserColumn.__init__(self, win, 0, tab=None) 
    
    def _draw_directory(  # pylint: disable=too-many-locals,too-many-branches,too-many-statements
            self):
        """Draw the contents of a directory"""
        if self.image:
            self.image = None
            self.need_clear_image = True
            Pager.clear_image(self)

        if self.level > 0 and not self.settings.preview_directories:
            return

        base_color = ['in_browser']

        if self.fm.ui.viewmode == 'multipane' and self.tab is not None:
            active_pane = self.tab == self.fm.thistab
            if active_pane:
                base_color.append('active_pane')
            else:
                base_color.append('inactive_pane')
        else:
            active_pane = False

        self.win.move(0, 0)

        if not self.target.content_loaded:
            self.color(tuple(base_color))
            self.addnstr("...", self.wid)
            self.color_reset()
            return

        if self.main_column:
            base_color.append('main_column')

        if not self.target.accessible:
            self.color(tuple(base_color + ['error']))
            self.addnstr("not accessible", self.wid)
            self.color_reset()
            return

        if self.target.empty():
            self.color(tuple(base_color + ['empty']))
            self.addnstr("empty", self.wid)
            self.color_reset()
            return

        self._set_scroll_begin()

        copied = [f.path for f in self.fm.copy_buffer]

        # Set the size of the linum text field to the number of digits in the
        # visible files in directory.
        linum_text_len = len(str(self.scroll_begin + self.hei))
        linum_format = "{0:>" + str(linum_text_len) + "}"
        # add separator between line number and tag
        linum_format += " "

        selected_i = self._get_index_of_selected_file()
        for line in range(self.hei):
            i = line + self.scroll_begin

            try:
                drawn = self.target.files[i]
            except IndexError:
                break

            tagged = self.fm.tags and drawn.realpath in self.fm.tags
            if tagged:
                tagged_marker = self.fm.tags.marker(drawn.realpath)
            else:
                tagged_marker = " "

            # Extract linemode-related information from the drawn object
            metadata = None
            current_linemode = drawn.linemode_dict[drawn.linemode]
            if current_linemode.uses_metadata:
                metadata = self.fm.metadata.get_metadata(drawn.path)
                if not all(getattr(metadata, tag)
                           for tag in current_linemode.required_metadata):
                    current_linemode = drawn.linemode_dict[linemode.DEFAULT_LINEMODE]

            metakey = hash(repr(sorted(metadata.items()))) if metadata else 0
            key = (self.wid, selected_i == i, drawn.marked, self.main_column,
                   drawn.path in copied, tagged_marker, drawn.infostring,
                   drawn.vcsstatus, drawn.vcsremotestatus, self.target.has_vcschild,
                   self.fm.do_cut, current_linemode.name, metakey, active_pane,
                   self.settings.line_numbers)

            # Check if current line has not already computed and cached
            if key in drawn.display_data:
                # Recompute line numbers because they can't be reliably cached.
                if self.main_column and self.settings.line_numbers != 'false':
                    line_number_text = self._format_line_number(linum_format,
                                                                i,
                                                                selected_i)
                    drawn.display_data[key][0][0] = line_number_text

                self.execute_curses_batch(line, drawn.display_data[key])
                self.color_reset()
                continue

            text = current_linemode.filetitle(drawn, metadata)

            if drawn.marked and (self.main_column
                                 or self.settings.display_tags_in_all_columns):
                text = " " + text

            # Computing predisplay data. predisplay contains a list of lists
            # [string, colorlst] where string is a piece of string to display,
            # and colorlst a list of contexts that we later pass to the
            # colorscheme, to compute the curses attribute.
            predisplay_left = []
            predisplay_right = []
            space = self.wid

            # line number field
            if self.settings.line_numbers != 'false':
                if self.main_column and space - linum_text_len > 2:
                    line_number_text = self._format_line_number(linum_format,
                                                                i,
                                                                selected_i)
                    predisplay_left.append([line_number_text, []])
                    space -= linum_text_len

                    # Delete one additional character for space separator
                    # between the line number and the tag
                    space -= 1

            # selection mark
            tagmark = self._draw_tagged_display(tagged, tagged_marker)
            tagmarklen = self._total_len(tagmark)
            if space - tagmarklen > 2:
                predisplay_left += tagmark
                space -= tagmarklen

            # vcs data
            vcsstring = self._draw_vcsstring_display(drawn)
            vcsstringlen = self._total_len(vcsstring)
            if space - vcsstringlen > 2:
                predisplay_right += vcsstring
                space -= vcsstringlen

            # info string
            infostring = []
            infostringlen = 0
            try:
                infostringdata = current_linemode.infostring(drawn, metadata)
                if infostringdata:
                    infostring.append([" " + infostringdata + " ",
                                       ["infostring"]])
            except NotImplementedError:
                infostring = self._draw_infostring_display(drawn, space)
            if infostring:
                infostringlen = self._total_len(infostring)
                if space - infostringlen > 2:
                    predisplay_right = infostring + predisplay_right
                    space -= infostringlen

            textstring = self._draw_text_display(text, space)
            textstringlen = self._total_len(textstring)
            predisplay_left += textstring
            space -= textstringlen

            assert space >= 0, "Error: there is not enough space to write the text. " \
                "I have computed spaces wrong."
            if space > 0:
                predisplay_left.append([' ' * space, []])

            # Computing display data. Now we compute the display_data list
            # ready to display in curses. It is a list of lists [string, attr]

            this_color = base_color + list(drawn.mimetype_tuple) + \
                self._draw_directory_color(i, drawn, copied)
            display_data = []
            drawn.display_data[key] = display_data

            drawn, this_color = hook_before_drawing(drawn, this_color)

            predisplay = predisplay_left + predisplay_right
            for txt, color in predisplay:
                attr = self.settings.colorscheme.get_attr(*(this_color + color))
                display_data.append([txt, attr])

            self.execute_curses_batch(line, display_data)
            self.color_reset()
