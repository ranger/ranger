from __future__ import absolute_import

import py2_compat

import astroid
import pylint.testutils
from pylint.interfaces import HIGH

from sys import version_info
PY2 = version_info[0] < 3


class TestPy2CompatibilityChecker(pylint.testutils.CheckerTestCase):
    CHECKER_CLASS = py2_compat.Py2CompatibilityChecker

    def test_oldstyle_class(self):
        oldstyle_class, from_old = astroid.extract_node("""
        class OldStyle(): #@
            pass

        class FromOld(OldStyle): #@
            pass
        """)

        with self.assertAddsMessages(
            pylint.testutils.MessageTest(
                msg_id='old-style-class',
                node=oldstyle_class,
                confidence=HIGH,
            ),
            ignore_position=True,
        ):
            self.checker.visit_classdef(oldstyle_class)

        with self.assertNoMessages():
            self.checker.visit_classdef(from_old)

    def test_newstyle_class(self):
        newstyle_class, from_new = astroid.extract_node("""
        class NewStyle(object): #@
            pass
        class FromNew(NewStyle): #@
            pass
        """)

        with self.assertNoMessages():
            self.checker.visit_classdef(newstyle_class)
            self.checker.visit_classdef(from_new)

    def test_print_without_import(self):
        if PY2:
            return

        print_function_call = astroid.extract_node("""
        print("Print function call without importing print_function")
        """)

        with self.assertAddsMessages(
            pylint.testutils.MessageTest(
                msg_id='print-without-import',
                node=print_function_call,
                confidence=HIGH,
            ),
            ignore_position=True,
        ):
            self.checker.visit_call(print_function_call)

    def test_print_with_import(self):
        print_function_call = astroid.extract_node("""
        from __future__ import print_function
        print("Print function call with importing print_function") #@
        """)

        nested_print_function_call = astroid.extract_node("""
        def f():
            from __future__ import print_function
            class A():
                def m(self):
                    print("Nested print with import in scope") #@
        """)

        with self.assertNoMessages():
            self.checker.visit_call(print_function_call)
            self.checker.visit_call(nested_print_function_call)

    def test_print_late_import(self):
        if PY2:
            return

        early_print_function_call = astroid.extract_node("""
        print("Nested print with import in scope") #@
        def f():
            from __future__ import print_function
            class A():
                def m(self):
                    pass
        """)

        with self.assertAddsMessages(
            pylint.testutils.MessageTest(
                msg_id='print-without-import',
                node=early_print_function_call,
                confidence=HIGH,
            ),
            ignore_position=True,
        ):
            self.checker.visit_call(early_print_function_call)

    def test_implicit_format_spec(self):
        if PY2:
            return

        implicit_format_spec = astroid.extract_node("""
        "{}".format("implicit") #@
        """)

        with self.assertAddsMessages(
            pylint.testutils.MessageTest(
                msg_id='implicit-format-spec',
                node=implicit_format_spec,
                confidence=HIGH,
            ),
            ignore_position=True,
        ):
            self.checker.visit_call(implicit_format_spec)

    def test_with_Popen(self):
        with_subprocess_Popen, with_Popen, with_Popen23 = astroid.extract_node("""
        import subprocess
        with subprocess.Popen(): #@
            pass

        from subprocess import Popen
        with Popen(): #@
            pass

        from ranger.ext.popen23 import Popen23
        with Popen23(): #@
            pass
        """)

        with self.assertAddsMessages(
            pylint.testutils.MessageTest(
                msg_id='with-popen23',
                node=with_Popen,
                confidence=HIGH,
            ),
            ignore_position=True,
        ):
            self.checker.visit_with(with_subprocess_Popen)
            self.checker.visit_with(with_Popen)
        with self.assertNoMessages():
            self.checker.visit_with(with_Popen23)

    def test_use_format(self):
        old_format, new_format, f_string = astroid.extract_node("""
            "2 + 2 is %s" % (2+2) #@
            "2 + 2 is {0}".format(2+2) #@
            f"2 + 2 is {2+2}" #@
        """)

        with self.assertAddsMessages(
            pylint.testutils.MessageTest(
                msg_id='use-format-method',
                node=f_string,
                confidence=HIGH,
            ),
            ignore_position=True,
        ):
            self.checker.visit_joinedstr(f_string)
        with self.assertNoMessages():
            self.checker.visit_joinedstr(old_format)
            self.checker.visit_joinedstr(new_format)

    # # These checks still exist as old-division and no-absolute-import
    # def test_division_without_import(self):
    #     division = astroid.extract_node("""
    #     5/2
    #     """)

    #     with self.assertAddsMessages(
    #         pylint.testutils.MessageTest(
    #             msg_id='division-without-import',
    #             node=division,
    #         ),
    #     ):
    #         self.checker.visit_XXX(division)

    # def test_division_with_import(self):
    #     division = astroid.extract_node("""
    #     from __future__ import division
    #     5/2 #@
    #     """)

    #     with self.assertNoMessages():
    #         self.checker.visit_XXX(division)

    # def test_absolute_import(self):
    #     no_import = astroid.extract_node("""
    #     import sys
    #     """)

    #     with self.assertAddsMessages(
    #         pylint.testutils.MessageTest(
    #             msg_id='old-no-absolute-import',
    #             node=no_import,
    #         ),
    #     ):
    #         self.checker.visit_XXX(no_import)

    #     only_import = astroid.extract_node("""
    #     from __future__ import absolute_import
    #     """)

    #     first_import = astroid.extract_node("""
    #     from __future__ import absolute_import, print_function
    #     """)

    #     second_import = astroid.extract_node("""
    #     from __future__ import print_function, absolute_import
    #     """)

    #     with self.assertNoMessages():
    #         self.checker.visit_XXX(only_import)
    #         self.checker.visit_XXX(first_import)
    #         self.checker.visit_XXX(second_import)
