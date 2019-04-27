"""Rez installer.

"""
import os
import sys
import gzip
import errno
import tarfile
import argparse
import subprocess

HOME = os.path.expanduser("~")
REZ_HOME = os.path.join(HOME, ".rez")

SCRIPTS = {
    # Key is the script to create and value is the cli module to use.
    "_rez_fwd": "forward",
    "_rez-complete": "complete",
    "rez": "rez",
    "rez-bind": "bind",
    "rez-build": "build",
    "rez-config": "config",
    "rez-context": "context",
    "rez-cp": "cp",
    "rez-depends": "depends",
    "rez-diff": "diff",
    "rez-env": "env",
    "rez-gui": "gui",
    "rez-help": "help",
    "rez-interpret": "interpret",
    "rez-memcache": "memcache",
    "rez-pip": "pip",
    "rez-plugins": "plugins",
    "rez-python": "python",
    "rez-release": "release",
    "rez-search": "search",
    "rez-selftest": "selftest",
    "rez-status": "status",
    "rez-suite": "suite",
    "rez-test": "test",
    "rez-view": "view",
    "rez-yaml2py": "yaml2py",
    "rezolve": ""
}

SCRIPT_TEMPLATE = """#!/usr/bin/env python2
import os
import sys

lib_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lib'))

sys.path.insert(0, lib_path)

from rez.cli._main import run

run({0!r})
"""


class RezInstaller(object):
    def __init__(self, version=None, path=None, target=None):
        self._version = version
        self._artifact_path = path
        self._target = target or REZ_HOME

    def run(self):
        self.ensure_home()
        try:
            self.install(self._version, self._artifact_path)
        except subprocess.CalledProcessError as e:
            return e.returncode

        return 0

    def ensure_home(self):
        """Ensures that REZ_HOME exists or create it."""
        if not os.path.exists(REZ_HOME):
            os.mkdir(REZ_HOME, 0o755)

    def install(self, version, path):
        """Installs Poetry in REZ_HOME."""
        print "Installing version {0!r}".format(version or path)

        self.make_lib(version, path)
        self.make_bin(path)
        # self.make_env()

    def make_lib(self, version, path):
        """"""
        if version:
            # Fetch from GitHub
            # And store the new path into path var.
            pass

        lib_path = os.path.join(self._target, "lib")
        try:
            os.makedirs(lib_path, 0o755)
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise

        gz = gzip.GzipFile(path, mode="rb")
        try:
            with tarfile.TarFile(path, fileobj=gz, format=tarfile.PAX_FORMAT) as fh:
                fh.extractall(lib_path)
        finally:
            gz.close()

    def make_bin(self, path):
        """"""
        bin_path = os.path.join(self._target, "bin")
        try:
            os.makedirs(bin_path, 0o755)
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise

        for script, command in SCRIPTS.items():
            script_content = SCRIPT_TEMPLATE.format(command)
            script_path = os.path.join(bin_path, script)
            with open(script_path, "wb") as fh:
                fh.write(script_content)

            os.chmod(script_path, 0o755)


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()

    group.add_argument(
        "-t",
        "--tar",
        help="Path to an arcchive to install from. "
             "If not specified, GitHub will be used.",
        metavar=""
    )
    group.add_argument(
        "--version",
        help="Rez version to install.",
        metavar=""
    )
    group.add_argument(
        "--latest",
        help="Install the latest version available.",
        metavar=""
    )

    parser.add_argument(
        "--target",
        # default=REZ_HOME,
        default="/var/tmp/rez",
        help="Target directory in which to install Rez into. "
        "If not specified, Rez will be installed in {0!r}".format(REZ_HOME),
        metavar=""
    )

    args = parser.parse_args()

    if not any([args.version, args.tar, args.latest]):
        raise parser.error("One of --tar, --version or --latest needs to be specified.")

    installer = RezInstaller(
        version=args.version or args.latest,
        path=args.tar,
        target=args.target
    )
    return installer.run()


if __name__ == "__main__":
    sys.exit(main())
