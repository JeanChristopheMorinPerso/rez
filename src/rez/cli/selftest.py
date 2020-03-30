'''
Run unit tests.
'''

import inspect
import os
import argparse
from pkgutil import iter_modules

cli_dir = os.path.dirname(inspect.getfile(inspect.currentframe()))
src_rez_dir = os.path.dirname(cli_dir)
tests_dir = os.path.join(src_rez_dir, 'tests')

all_module_tests = []

def setup_parser(parser, completions=False):
    parser.add_argument(
        "tests", metavar="NAMED_TEST", default=[], nargs="*",
        help="a specific test module/class/method to run; may be repeated "
        "multiple times; if no tests are given, through this or other flags, "
        "all tests are run")
    parser.add_argument(
        "-s", "--only-shell", metavar="SHELL",
        help="limit shell-dependent tests to the specified shell")

    # Find tests
    tests = []
    prefix = "test_"
    for importer, name, ispkg in iter_modules([tests_dir]):
        if not ispkg and name.startswith(prefix):
            module = importer.find_module(name).load_module(name)
            name_ = name[len(prefix):]
            all_module_tests.append(name_)
            tests.append((name_, module))

    group = parser.add_argument_group("tests")
    # create argparse entry for each module's unit test
    for name, module in sorted(tests):
        group.add_argument(
            "--%s" % name, action="append_const",
            dest='module_tests', default=[], const=name,
            help=module.__doc__.strip().rstrip('.')
        )


def command(opts, parser, extra_arg_groups=None):
    import sys

    import pytest

    os.environ["__REZ_SELFTEST_RUNNING"] = "1"

    if opts.only_shell:
        os.environ["__REZ_SELFTEST_SHELL"] = opts.only_shell

    if not opts.module_tests and not opts.tests:
        module_tests = all_module_tests
    else:
        module_tests = opts.module_tests

    dirname = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    tests = []
    for module in sorted(module_tests):
        tests.append(os.path.join(dirname, 'tests', 'test_{0}.py'.format(module)))
    tests += opts.tests

    pytest.main(tests)


# Copyright 2013-2016 Allan Johns.
#
# This library is free software: you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library.  If not, see <http://www.gnu.org/licenses/>.
