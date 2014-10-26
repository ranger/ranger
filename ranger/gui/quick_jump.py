from ranger.core.shared import SettingsAware
import ranger
import math

BASE10 = "0123456789"

def baseconvert(number, fromdigits, todigits):
    # make an integer value out of the number
    value = 0
    for digit in str(number):
        value = value * len(fromdigits) + fromdigits.index(digit)
                
    # create the result in base 'len(todigits)'
    if value == 0:
        res = todigits[0]
    else:
        res = ""
        while value > 0:
            digit = value % len(todigits)
            res = todigits[digit] + res
            value = int(value / len(todigits))
                        
    return res


class QuickJump:
    def __init__(self, fm=None):
        self.activated = False
        self.ignore_case = False
        self.paused = False
        # the already entered keys 
        self.key_sequence = ""
        # the length of the key sequence needed to determine a line
        self.levels = 0
        if fm is not None:
            self.fm = fm

    def activate(self, scout):
        def _ignore_case_check():
            ignore_case = self.scout.IGNORE_CASE in self.scout.flags
            if self.ignore_case is not ignore_case:
                self.ignore_case = ignore_case
                self.fm.ui.browser.main_column.request_redraw()                

        self.scout = scout
        settings = self.fm.settings
        newState = scout.QUICK_JUMP in scout.flags
        _ignore_case_check()
        if self.activated != newState:
            self.activated = newState
            self.fm.ui.browser.main_column.request_redraw()
            self.key_sequence = ""
            self.paused = False
            if len(settings.quick_jump_letters) < 2:
                settings.quick_jump_letters = "fdsartgbvecwxqyiopmnhzulkj"

    def deactivate(self):
        self.activated = False

    def toggle_paused(self):
        self.paused = not self.paused
        self.fm.ui.browser.main_column.request_redraw()

    def __upper_lower(self, s):
        if self.scout.IGNORE_CASE in self.scout.flags:
            return s.upper()
        return s.lower()

    def draw_display(self, line, numFiles):
        letter = self.calc_next_letter(line, numFiles)
        return [[letter, ['quick_jump']]]

    def calc_next_letter(self, line, numFiles):
        def _calc_base():
            maxNumLetters = len(self.fm.settings.quick_jump_letters)
            self.levels = int(math.log(numFiles) / math.log(maxNumLetters)) + 1
            numLetters = int(math.ceil(math.pow(numFiles, float(1)/self.levels)))
            return self.fm.settings.quick_jump_letters[0:numLetters] 

        if not self.activated:
            return ""

        if self.paused:
            return "-"

        self.letter_base = _calc_base()
        in_letter_base = baseconvert(line, BASE10, self.letter_base)
        # add leadings 'zeros'
        while len(in_letter_base) < self.levels:
            in_letter_base = self.letter_base[0] + in_letter_base

        if self.fm.settings.quick_jump_reverse_seq:
            in_letter_base = in_letter_base[::-1]

        seq = self.key_sequence
        if seq.lower() == in_letter_base.lower()[0:len(seq)]:
            return self.__upper_lower(in_letter_base[len(seq)])
        return " "


    def press(self, key):
        # helper functions
        def _move():
            target = self.fm.ui.browser.main_column.target
            seq = self.key_sequence.lower()
            if self.fm.settings.quick_jump_reverse_seq:
                seq = seq[::-1]
            line = int(baseconvert(seq, self.letter_base.lower(), BASE10))
            self.fm.move(to = line + self.fm.ui.browser.main_column.scroll_begin)
            self.key_sequence = ""
            if self.scout.AUTO_OPEN in self.scout.flags: 
                if self.scout.MARK in self.scout.flags:
                    self.fm.mark_files(toggle=True)
                else:
                    if target.files[target.pointer].is_directory:
                        self.fm.move(right = 1)

            if not self.scout.KEEP_OPEN in self.scout.flags:
                self.fm.ui.console.close(True)

        # main function
        if not self.activated:
            return False

        self.fm.ui.keymaps.use_keymap('quick_jump')
        if self.fm.ui.press(key):
            return True

        # return key
        if key == 10 and self.scout.MARK in self.scout.flags:                
            self.fm.mark_files(toggle=True)
            return True

        if self.paused or key > 255 or \
                  not chr(key) in self.__upper_lower(self.letter_base):
            return False

        self.key_sequence = self.key_sequence + chr(key)
        self.fm.ui.browser.main_column.request_redraw()

        if len(self.key_sequence) == self.levels:
            _move()

        return True
