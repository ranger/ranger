# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

"""
filetree.py - Compare File structures

Module Containing the Filetree class to represent
a file directory structure.

The Module does also provide the nesecarry routines
to compare these filetrees against each other.
"""

import os
from hashlib import md5


class EmptyList(Exception):
    pass


class FileTree:
    """ The FileTree class represents the files in a filetree.

        :param path: str with the path to directory
        :param name: str with a name for the filetree object

    """

    def __init__(self, path, name=""):

        self.name = name    # identifier name of the tree.
        self._path = path    # absolute path to the root directory.

        # parse the different ways of specifying a dir.
        if path[-1] == "/":
            path = path[0:-1]

        # leading path is the path leading up to the root
        # directory.  Directory is the name of the root directory.
        self.leading_path, self.directory = seperate_path(self._path)

        # file tree is a walk generator object.
        self._file_tree = os.walk(self._path)

        # file_list is a list of the underlying filesystem
        # structure from with the absolute path
        self._file_list = create_filelist(self._file_tree)

        # filenames are the files relative to the root dir.
        self._name_list = self._create_namelist()

        if not self._file_list:
            raise EmptyList("List of files is empty")

        self._file_list.sort()

    def __repr__(self):
        return "FileTree object named: <{}>.\n" \
               "Root: <{}>\n" \
               "Elements: <{}>".format(self.name, self._path, self.size)

    def __len__(self):
        return self.size



    def _create_namelist(self):
        """makes a list for all files in the tree
        relative to the root directory.

        :return: list with files in tree relative to the root.

        """
        file_names = []

        for path in self._file_list:
            # strip the leading path from the file_list.
            # /leading/path/to/root/with/file -> root/with/file
            plength = len(self.leading_path + self.directory) + 1
            file_names.append(path[plength:])
        return file_names

    def compare(self, tree, comp, verbose=False):
        """ compare the filetree against another filetree.

        :param: tree: FileTree object to compare against.
        :param: comp: str comparison type (size, set, bin)
        :param: verbose: print diffs.

        :return: dict with comparison results.
        """

        if comp == "size":
            res = size_comp(self, tree, verbose)

        if comp == "set":
            res = set_comp(self, tree, verbose)

        if comp == "bin":
            res = bin_comp(self, tree, verbose=verbose)

        return res

    @property
    def filenames(self):
        """ property holding tree filenames """
        return self._name_list

    @property
    def files(self):
        """ property holding list of files """
        return self._file_list

    @property
    def size(self):
        """ property returning the elements in tree """
        return len(self._file_list)

    @property
    def path(self):
        """ property providing the absolute path to the
        root directory of the filetree.
        """
        return self._path

    @path.setter
    def path(self, path):
        if path.startswith("./"):
            self._path = os.path.abspath(path)
        else:
            self._path = path


def size_comp(tree_a, tree_b, verbose=False):
    """Analyze if there is a difference of number of files
    in the two trees

    :param tree_a: FileTree obj with files in tree A.
    :param tree_b: FileTree obj with files in tree B.

    :return: result dict with two fields.
             "res": bool. Comparison outcome
             "nfiles": list. number of files in dir a and b
                       respectively.

    """

    result = {"res": 0, "nfiles": [0, 0]}

    size_a = tree_a.size
    size_b = tree_b.size

    result["nfiles"] = [size_a, size_b]

    name_a = tree_a.name
    name_b = tree_b.name

    if name_a == "":
        name_a = "a"

    if name_b == "":
        name_b = "b"

    if size_a == size_b:
        if verbose:
            print("[OK] - same number of elements: {}".format(size_a))
        result["res"] = True
    else:
        if verbose:
            print("[FAILED] - different number of elements in both trees")
            print('{}: {} \n{}: {}'.format(name_a, size_a, name_b, size_b))
        result["res"] = False

    return result


def set_comp(tree_a, tree_b, verbose=False):
    """ Compare to filetree sets

    :param set_a: first set for comparison
    :param set_b: second set for comparison

    :return: result dict with three fields.
             "res": bool. Comparison outcome
             "mis_a": list. files missing in folder a
             "mis_b": list. files missing in folder b

    """
    result = {"res": 0, "mis_a": [], "mis_b": []}

    set_a = set(tree_a.filenames)
    set_b = set(tree_b.filenames)

    if set_a == set_b:
        if verbose:
            print("[OK] - Same filenames in both trees.")
        result["res"] = True
    else:

        diff_a = list(set_b.difference(set_a))
        diff_b = list(set_a.difference(set_b))

        if verbose:
            print("[FAILED] - Missing in <{}>:".format(tree_a.path))
            print("\n".join(diff_a))
            print("[FAILED] - Missing in <{}>:".format(tree_b.path))
            print("\n".join(diff_b))

        result["res"] = False
        result["mis_a"] = diff_a
        result["mis_b"] = diff_b

    return result


def bin_comp(tree_a, tree_b, method=md5, verbose=False):
    """Analyze any difference in the files in the tree. This analysis
    is based on a binary comparision between the two trees.

    :param tree_a: FileTree obj with files in tree A.
    :param tree_b: FileTree obj with files in tree B.
    :param method: provide a hash function to compare binary
                   file content. (md5, sha1, sha256)

    :return: result dict with two fields.
             "res": bool. Comparison outcome
             "diff": list. Differing files between the two dirs.

    """
    diff = []
    result = {"res": False, "diff": []}

    try:
        for file_a, file_b in zip(tree_a.files, tree_b.files):
            h_a = _hash(file_a, method)
            h_b = _hash(file_b, method)
            if h_a != h_b:
                tmp = file_a.split(tree_a.leading_path)[1]
                diff.append(tmp.split((tree_a.directory + "/"))[1])

    except FileNotFoundError as err:
        print("Ensure the same elements are in both trees")
        print(err)

    else:
        if not diff:
            print("[OK] - Same binary file content:")
            result["res"] = True
        else:
            if verbose:
                print("[FAILED] - Binary Difference in: ")
                print("\n".join(diff))
            result["res"] = False

        result["diff"] = diff
        return result


def _hash(filepath, method):
    hasher = method()
    with open(filepath, 'rb') as file:
        chunk = 0
        while chunk != b'':
            chunk = file.read(1024)
            hasher.update(chunk)
    return hasher.hexdigest()


def seperate_path(path):
    """ Seperate the leading path and the directory of
    interest. /leading/path/to/directory

    :param path: str with the path to seperate

    :return: tuple with (leading_path, directory)

    """

    path_elements = path.split("/")
    leading_path = "/" + "/".join(path_elements[1:-1]) + "/"
    if path_elements[-1] == '':
        directory = path_elements[-2]
    else:
        directory = path_elements[-1]
    return leading_path, directory

def create_filelist(tree):
    """makes a list for all files in the tree.

    :param tree: generator walk object containing the file tree.

    :return: list with files in tree.

    """
    file_list = []
    for root, _dirs, files in tree:
        for entry in files:
            if root:
                file_list.append("{}/{}".format(root, entry))
            else:
                file_list.append("{}".format(entry))
    return file_list
