from __future__ import absolute_import

from ranger.gui import ui


class Settings(object):
    update_tmux_title = True


class FileManager(object):
    def __init__(self):
        self.notifications = []

    def notify(self, message, bad=False):
        self.notifications.append((message, bad))


def test_handle_multiplexer_missing_screen_executable(monkeypatch):
    monkeypatch.setattr(ui, '_in_tmux', lambda: False)
    monkeypatch.setattr(ui, '_in_screen', lambda: True)

    def missing_screen(*args, **kwargs):
        raise OSError(2, 'No such file or directory')

    monkeypatch.setattr(ui, 'check_output', missing_screen)

    file_manager = FileManager()
    user_interface = ui.UI(fm=file_manager)
    user_interface.settings = Settings()

    user_interface.handle_multiplexer()

    assert user_interface._multiplexer_title
    assert file_manager.notifications == [(
        "Couldn't access previous multiplexer window name, "
        "won't be able to restore.",
        False,
    )]
