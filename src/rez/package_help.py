from rez.packages import iter_packages
from rez.config import config
from rez.util import AttrDictWrapper, ObjectStringFormatter, \
    convert_old_command_expansions
import subprocess
import webbrowser
import os.path
import sys


class PackageHelp(object):
    """Object for extracting and viewing help for a package.

    Given a package and version range, help will be extracted from the latest
    package in the version range that provides it.
    """
    def __init__(self, package_name, version_range=None, paths=None, verbose=False):
        """Create a PackageHelp object.

        Args:
            package_name (str): Package to search.
            version_range (`VersionRange`): Versions to search.
        """
        self.package = None
        self._verbose = verbose
        self._sections = []

        # find latest package with a help entry
        package = None
        it = iter_packages(package_name, range=version_range)
        packages = sorted(it, key=lambda x: x.version, reverse=True)
        for package_ in packages:
            if self._verbose:
                print "searching for help in %s..." % str(package_)
            if package_.help:
                package = package_
                break

        if package:
            help_ = package.help
            if isinstance(help_, basestring):
                sections = [["Help", help_]]
            elif isinstance(help_, list):
                sections = help_
            if self._verbose:
                print "found %d help entries in %s." % (len(sections), str(package))

            # create string formatter for help entries
            if package.num_variants == 0:
                base = os.path.dirname(package.path)
                root = base
            else:
                variant = package.get_variant(0)
                base = variant.base
                root = variant.root

            namespace = dict(base=base, root=root, config=config)
            formatter = ObjectStringFormatter(AttrDictWrapper(namespace),
                                              expand='unchanged')

            # format sections
            for section in sections:
                uri = section[1]
                uri = convert_old_command_expansions(uri)
                uri = uri.replace("$BROWSER", "").strip()
                uri = formatter.format(uri)
                section[1] = uri

            self.package = package
            self._sections = sections

    @property
    def success(self):
        """Return True if help was found, False otherwise."""
        return bool(self._sections)

    @property
    def sections(self):
        """Returns a list of (name, uri) 2-tuples."""
        return self._sections

    def open(self, section_index=0):
        """Launch a help section."""
        uri = self._sections[section_index][1]
        if len(uri.split()) == 1:
            self._open_url(uri)
        else:
            if self._verbose:
                print "running command: %s" % uri
            subprocess.Popen(uri, shell=True).wait()

    def print_info(self, buf=None):
        """Print help sections."""
        buf = buf or sys.stdout
        print >> buf, "Sections:"
        for i, section in enumerate(self._sections):
            print >> buf, "  %s:\t%s (%s)" % (i + 1, section[0], section[1])

    @classmethod
    def open_rez_manual(cls):
        """Open the Rez user manual."""
        self._open_url(config.documentation_url)

    @classmethod
    def _open_url(cls, url):
        if config.browser:
            cmd = [config.browser, url]
            if self._verbose:
                print "running command: %s" % " ".join(cmd)
            subprocess.Popen(cmd).communicate()
        else:
            if self._verbose:
                print "opening URL in browser: %s" % url
            webbrowser.open_new(url)