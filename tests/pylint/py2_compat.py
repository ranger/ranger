from __future__ import absolute_import

import astroid

from pylint.checkers import BaseChecker
from pylint.interfaces import IAstroidChecker, HIGH

from pylint.checkers import utils


class Py2CompatibilityChecker(BaseChecker):
    """Verify some simple properties of code compatible with both 2 and 3"""

    __implements__ = IAstroidChecker

    # The name defines a custom section of the config for this checker.
    name = "py2-compat"
    # The priority indicates the order that pylint will run the checkers.
    priority = -1
    # This class variable declares the messages (ie the warnings and errors)
    # that the checker can emit.
    msgs = {
        # Each message has a code, a message that the user will see,
        # a unique symbol that identifies the message,
        # and a detailed help message
        # that will be included in the documentation.
        "E4200": ('Use explicit inheritance from "object"',
                  "old-style-class",
                  'Python 2 requires explicit inheritance from "object"'
                  ' for new-style classes.'),
        # old-division
        # "E4210": ('Use "//" for integer division or import from "__future__"',
        #     "division-without-import",
        #     'Python 2 might perform integer division unless you import'
        #     ' "division" from "__future__".'),
        # no-absolute-import
        # "E4211": ('Always import "absolute_import" from "__future__"',
        #     "old-no-absolute-import",
        #     'Python 2 allows relative imports unless you import'
        #     ' "absolute_import" from "__future__".'),
        "E4212": ('Import "print_function" from "__future__"',
                  "print-without-import",
                  'Python 2 requires importing "print_function" from'
                  ' "__future__" to use the "print()" function syntax.'),
        "E4220": ('Use explicit format spec numbering',
                  "implicit-format-spec",
                  'Python 2.6 does not support implicit format spec numbering'
                  ' "{}", use explicit numbering "{0}" or keywords "{key}".')
    }
    # This class variable declares the options
    # that are configurable by the user.
    options = ()

    def visit_classdef(self, node):
        """Make sure classes explicitly inherit from object"""
        if not node.bases and node.type == 'class' and not node.metaclass():
            # We use confidence HIGH here because this message should only ever
            # be emitted for classes at the root of the inheritance hierarchy
            self.add_message('old-style-class', node=node, confidence=HIGH)

    def visit_call(self, node):
        """Make sure "print_function" is imported if necessary"""
        if (isinstance(node.func, astroid.nodes.Name)
                and node.func.name == "print"):
            if "print_function" in node.root().future_imports:
                def previous(node):
                    if node is not None:
                        parent = node.parent
                    previous = node.previous_sibling()
                    if previous is None:
                        return parent
                    return previous

                prev = previous(node)
                while prev is not None:
                    if (isinstance(prev, astroid.nodes.ImportFrom)
                        and prev.modname == "__future__"
                        and "print_function" in (name_alias[0] for name_alias in
                                                 prev.names)):
                        return
                    prev = previous(prev)

                self.add_message("print-without-import", node=node,
                                 confidence=HIGH)
            else:
                self.add_message("print-without-import", node=node,
                                 confidence=HIGH)

        func = utils.safe_infer(node.func)
        if (
            isinstance(func, astroid.BoundMethod)
            and isinstance(func.bound, astroid.Instance)
            and func.bound.name in ("str", "unicode", "bytes")
        ):
            if func.name == "format":
                if isinstance(node.func, astroid.Attribute) and not isinstance(
                    node.func.expr, astroid.Const
                ):
                    return
                if node.starargs or node.kwargs:
                    return
                try:
                    strnode = next(func.bound.infer())
                except astroid.InferenceError:
                    return
                if not (isinstance(strnode, astroid.Const) and isinstance(
                        strnode.value, str)):
                    return
                try:
                    fields, num_args, manual_pos = (
                        utils.parse_format_method_string(strnode.value)
                    )
                except utils.IncompleteFormatString:
                    self.add_message("bad-format-string", node=node)
                if num_args != 0:
                    self.add_message("implicit-format-spec", node=node,
                                     confidence=HIGH)


def register(linter):
    """This required method auto registers the checker.

    :param linter: The linter to register the checker to.
    :type linter: pylint.lint.PyLinter
    """
    linter.register_checker(Py2CompatibilityChecker(linter))
