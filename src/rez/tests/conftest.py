import io
import os
import sys
import tempfile
import subprocess

import pytest

from rez.system import system
from rez.config import config, _create_locked_config
from rez.shells import get_shell_types, get_shell_class
from rez.utils.data_utils import deep_update

SHELLS = get_shell_types()
AVAILABLE_SHELLS = [
    x for x in SHELLS
    if get_shell_class(x).is_available()
]


def pytest_runtest_setup(item):
    """Function called by pytest for every test (item) discovered"""
    markers = [marker.name for marker in item.iter_markers()]
    if 'install_dependent' in markers:
        if os.getenv("__REZ_SELFTEST_RUNNING") or not system.is_production_rez_install:
            pytest.skip(
                "Must be run via 'rez-selftest' tool, see "
                "https://github.com/nerdvegas/rez/wiki/Installation#installation-script"
            )

    for marker in list(item.iter_markers(name='depends_on_program')):
        if not programs_exist(marker.args):
            pytest.skip(
                "Skipping because it was marked as dependent on %r but"
                " it wasn't found on the system." % marker.args[0]
            )


def programs_exist(programs):
    program_tests = {
        "cmake": ['cmake', '-h'],
        "make": ['make', '-h'],
        "g++": ["g++", "--help"]
    }

    for program in programs:
        command = program_tests.get(program)
        if not command:
            raise RuntimeError(
                "You asked for %r but we don't know how to call this program." % program
            )

        with open(os.devnull, 'wb') as DEVNULL:
            try:
                subprocess.check_call(command, stdout=DEVNULL, stderr=DEVNULL)
            except (OSError, IOError, subprocess.CalledProcessError):
                return False

    return True


@pytest.fixture(params=SHELLS)
def shell(request):
    """
    """
    if request.param not in AVAILABLE_SHELLS:
        pytest.skip('Shell %r is not available' % request.param)


@pytest.fixture(scope="session", autouse=True)
def stdin():
    """
    """
    original_stdin = sys.stdin
    fd, stdin_path = tempfile.mkstemp()
    stdin_file = io.open(fd, 'r')
    sys.stdin = io.TextIOWrapper(stdin_file)

    yield

    sys.stdin = original_stdin
    stdin_file.close()
    os.remove(stdin_path)


class Config(object):
    """
    """
    def __init__(self):
        self.conf = None
        self.settings = {}

    def setup(self, settings={}):
        print('Setting up config')
        self.conf = _create_locked_config(overrides=settings)
        config._swap(self.conf)

    def reset(self):
        """Reset to the initial config
        """
        print('Resetting config')
        config._swap(self.conf)
        self.conf = None

    def update(self, new_settings, override=False):
        """Can be called within test methods to modify settings on a
        per-test basis (as opposed cls.settings, which modifies it for all
        tests on the class)

        Note that multiple calls will not "accumulate" updates, but will
        instead patch the class's settings with the new_settings each time.

        new_settings : dict
            the updated settings to override the config with
        override : bool
            normally, the resulting config will be the result of merging
            the base cls.settings with the new_settings - ie, like doing
            cls.settings.update(new_settings).  If this is True, however,
            then the cls.settings will be ignored entirely, and the
            new_settings will be the only configuration settings applied
        """
        print('Updating config')
        self.reset()

        # ...then copy the class settings dict to instance, so we can
        # modify...
        if override:
            self.settings = dict(new_settings)
        else:
            self.settings = dict(settings)
            deep_update(self.settings, new_settings)

        # now swap the config back in...
        self.setup()


@pytest.fixture(scope="function")
def new_config():
    """
    """
    conf = Config()
    yield conf
    conf.reset()
