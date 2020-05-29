from ranger.container.directory import walklevel
import copy

def create_tree_no_symlinks(tmp_path):
    # ├── a
    # │   ├── c
    # │   │   └── file2.txt
    # │   └── file1.txt
    # └── b
    #     └── file3.txt
 
    a = tmp_path / 'a'
    a.mkdir()
    file1 = a / 'file1.txt'
    file1.touch()
    b = tmp_path / 'b'
    b.mkdir()

    c = a / 'c'
    c.mkdir()
    file2 = c / 'file2.txt'
    file2.touch()

    file3 = b / 'file3.txt'
    file3.touch()

def create_tree_with_symlinks_with_loop(tmp_path):
    # ├── a
    # │   ├── c
    # │   │   └── file2.txt
    # │   ├── file1.txt
    # │   └── link1 -> a
    # └── b
    #     └── file3.txt

    a = tmp_path / 'a'
    a.mkdir()
    file1 = a / 'file1.txt'
    file1.touch()
    symlink1 = a / 'link1'
    symlink1.symlink_to(a, target_is_directory=True)

    b = tmp_path / 'b'
    b.mkdir()

    c = a / 'c'
    c.mkdir()
    file2 = c / 'file2.txt'
    file2.touch()
 
    file3 = b / 'file3.txt'
    file3.touch()


def create_tree_with_symlinks_no_loop(tmp_path):
    # ├── a
    # │   ├── c
    # │   │   ├── file2.txt
    # │   │   └── link1 -> a/file1.txt
    # │   └── file1.txt
    # └── b
    #     └── file3.txt

    a = tmp_path / 'a'
    a.mkdir()
    file1 = a / 'file1.txt'
    file1.touch()
    b = tmp_path / 'b'
    b.mkdir()

    c = a / 'c'
    c.mkdir()
    file2 = c / 'file2.txt'
    file2.touch()

    file3 = b / 'file3.txt'
    file3.touch()
    symlink1 = c / 'link1'
    symlink1.symlink_to(file1)


def test_walklevel_all_levels_no_symlinks(tmp_path):
    create_tree_no_symlinks(tmp_path)

    walklevel_results = []
    for level in walklevel(str(tmp_path), -1):
        walklevel_results.append(copy.deepcopy(level))

    assert walklevel_results == [(str(tmp_path), ['a', 'b'], [],
                                  {'existance': False, 'path': ''}),
                                 (str(tmp_path / 'a'), ['c'], ['file1.txt'],
                                  {'existance': False, 'path': ''}),
                                 (str(tmp_path / 'a' / 'c'), [], ['file2.txt'],
                                  {'existance': False, 'path': ''}),
                                 (str(tmp_path / 'b'), [], ['file3.txt'],
                                  {'existance': False, 'path': ''})]


def test_walklevel_first_level_no_symlinks(tmp_path):
    create_tree_no_symlinks(tmp_path)

    walklevel_results = []
    for level in walklevel(str(tmp_path), 1):
        walklevel_results.append(copy.deepcopy(level))

    assert walklevel_results == [(str(tmp_path), ['a', 'b'], [],
                                  {'existance': False, 'path': ''}),
                                 (str(tmp_path / 'a'), ['c'], ['file1.txt'],
                                  {'existance': False, 'path': ''}),
                                 (str(tmp_path / 'b'), [], ['file3.txt'],
                                  {'existance': False, 'path': ''})]


def test_walklevel_all_levels_symlinks_with_loop(tmp_path):
    create_tree_with_symlinks_with_loop(tmp_path)

    walklevel_results = []
    for level in walklevel(str(tmp_path), -1, flat_follow_symlinks=True):
        walklevel_results.append(copy.deepcopy(level))

    assert walklevel_results == [(str(tmp_path), ['a', 'b'], [],
                                  {'existance': False, 'path': ''}),
                                 (str(tmp_path / 'a'), ['c'], ['file1.txt'],
                                  {'existance': True, 'path': str(tmp_path / 'a' / 'link1')}),
                                 (str(tmp_path / 'a' / 'c'), [], ['file2.txt'],
                                  {'existance': False, 'path': ''}),
                                 (str(tmp_path / 'b'), [], ['file3.txt'],
                                  {'existance': False, 'path': ''})]

def test_walklevel_first_level_symlinks_with_loop(tmp_path):
    create_tree_with_symlinks_with_loop(tmp_path)

    walklevel_results = []
    for level in walklevel(str(tmp_path), 1, flat_follow_symlinks=True):
        walklevel_results.append(copy.deepcopy(level))
    
    assert walklevel_results == [(str(tmp_path), ['a', 'b'], [],
                                  {'existance': False, 'path': ''}),
                                 (str(tmp_path / 'a'), ['c'], ['file1.txt'],
                                  {'existance': True, 'path': str(tmp_path / 'a' / 'link1')}),
                                 (str(tmp_path / 'b'), [], ['file3.txt'],
                                  {'existance': False, 'path': ''})]

def test_walklevel_all_levels_symlinks_without_loop(tmp_path):
    create_tree_with_symlinks_no_loop(tmp_path)

    walklevel_results = []
    for level in walklevel(str(tmp_path), -1, flat_follow_symlinks=True):
        walklevel_results.append(copy.deepcopy(level))
    
    assert walklevel_results == [(str(tmp_path), ['a', 'b'], [],
                                  {'existance': False, 'path': ''}),
                                 (str(tmp_path / 'a'), ['c'], ['file1.txt'],
                                  {'existance': False, 'path': ''}),
                                 (str(tmp_path / 'a' / 'c'), [], ['file2.txt', 'link1'],
                                  {'existance': False, 'path': ''}),
                                 (str(tmp_path / 'b'), [], ['file3.txt'],
                                  {'existance': False, 'path': ''})]

def test_walklevel_zero_level_no_symlinks(tmp_path):
    create_tree_no_symlinks(tmp_path)

    walklevel_results = []
    for level in walklevel(str(tmp_path), 0):
        walklevel_results.append(copy.deepcopy(level))
 
    assert walklevel_results == [(str(tmp_path), ['a', 'b'], [],
                                  {'existance': False, 'path': ''})]
