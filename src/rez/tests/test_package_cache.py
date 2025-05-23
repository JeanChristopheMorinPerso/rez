# SPDX-License-Identifier: Apache-2.0
# Copyright Contributors to the Rez Project


"""
Test package caching.
"""
import logging
import os
import os.path
import time
import subprocess

from rez.tests.util import TestBase, TempdirMixin, restore_os_environ, \
    install_dependent
from rez.packages import get_package
from rez.package_cache import PackageCache
from rez.resolved_context import ResolvedContext
from rez.exceptions import PackageCacheError
from rez.utils.filesystem import canonical_path


class TestPackageCache(TestBase, TempdirMixin):
    @classmethod
    def setUpClass(cls):
        TempdirMixin.setUpClass()

        cls.py_packages_path = canonical_path(cls.data_path("packages", "py_packages"))
        cls.solver_packages_path = canonical_path(cls.data_path("solver", "packages"))

        cls.package_cache_path = os.path.join(cls.root, "package_cache")
        os.mkdir(cls.package_cache_path)

        cls.settings = dict(
            packages_path=[cls.py_packages_path, cls.solver_packages_path],
            cache_packages_path=cls.package_cache_path,
            default_cachable=True,

            # ensure test packages will get cached
            package_cache_same_device=True,

            default_cachable_per_repository={
                cls.solver_packages_path: False
            },

            default_cachable_per_package={
                "late_binding": False
            }
        )

    @classmethod
    def tearDownClass(cls):
        TempdirMixin.tearDownClass()

    def _pkgcache(self):
        return PackageCache(self.package_cache_path)

    def test_cache_variant(self):
        """Test direct caching of a cachable variant."""
        pkgcache = self._pkgcache()

        package = get_package("versioned", "3.0")
        variant = next(package.iter_variants())

        _, status = pkgcache.add_variant(variant)
        self.assertEqual(status, PackageCache.VARIANT_CREATED)

        # adding again should indicate the variant is already cached
        _, status = pkgcache.add_variant(variant)
        self.assertEqual(status, PackageCache.VARIANT_FOUND)

    def test_delete_cached_variant(self):
        """Test variant deletion from cache."""
        pkgcache = self._pkgcache()

        package = get_package("versioned", "3.0")
        variant = next(package.iter_variants())

        pkgcache.add_variant(variant)

        result = pkgcache.remove_variant(variant)
        self.assertEqual(result, PackageCache.VARIANT_REMOVED)

        # another deletion should say not found
        result = pkgcache.remove_variant(variant)
        self.assertEqual(result, PackageCache.VARIANT_NOT_FOUND)

    def test_cache_fail_uncachable_variant(self):
        """Test that caching of an uncachable variant fails."""
        pkgcache = self._pkgcache()

        package = get_package("timestamped", "1.1.1")
        variant = next(package.iter_variants())

        with self.assertRaises(PackageCacheError):
            pkgcache.add_variant(variant)

    def test_cache_fail_no_variant_payload(self):
        """Test that adding a variant with no disk payload, fails."""
        pkgcache = self._pkgcache()

        package = get_package("variants_py", "2.0")
        variant = next(package.iter_variants())

        with self.assertRaises(PackageCacheError):
            pkgcache.add_variant(variant)

    def test_cache_fail_per_repo(self):
        """Test that caching fails on a package from a repo set to non-cachable."""
        pkgcache = self._pkgcache()

        package = get_package("pyfoo", "3.1.0")
        variant = next(package.iter_variants())

        with self.assertRaises(PackageCacheError):
            pkgcache.add_variant(variant)

    def test_cache_fail_per_package(self):
        """Test that caching fails on a package with a blacklisted name."""
        pkgcache = self._pkgcache()

        package = get_package("late_binding", "1.0")
        variant = next(package.iter_variants())

        with self.assertRaises(PackageCacheError):
            pkgcache.add_variant(variant)

    def test_external_logging_config(self):
        """Test that external logging is respected if configured."""
        config_file_path = canonical_path(self.data_path("config", "logging_config_test.conf"))
        with restore_os_environ():
            os.environ["REZ_LOGGING_CONF"] = config_file_path
            pkgcache = self._pkgcache()
            pkgcache._init_logging()
            logger = logging.getLogger('rez-pkg-cache')
            self.assertEqual(len(logger.handlers), 1)
            self.assertEqual(logger.handlers[0].__class__, logging.StreamHandler)
            self.assertEqual(logger.handlers[0].level, logging.DEBUG)

    @install_dependent()
    def test_caching_on_resolve(self):
        """Test that cache is updated as expected on resolved env."""
        pkgcache = self._pkgcache()

        with restore_os_environ():
            # set config settings into env so rez-pkg-cache proc sees them
            os.environ.update(self.get_settings_env())

            # Creating the context will asynchronously add variants to the cache
            # in a separate proc.
            # NOTE: pyfoo will not cache, because its repo is set to non-caching (see above)
            c = ResolvedContext([
                "timestamped-1.2.0",
                "pyfoo-3.1.0"
            ])

        # Prove that the resolved context used async mode.
        self.assertTrue(c.package_cache_async)

        variant = c.get_resolved_package("timestamped")

        # Retry 50 times with 0.1 sec interval, 5 secs is more than enough for
        # the very small variant to be copied to cache.
        cached_root = None
        resolve_not_always_cached = False
        for _ in range(50):
            cached_root = pkgcache.get_cached_root(variant)
            if cached_root:
                break

            resolve_not_always_cached = True
            time.sleep(0.1)

        self.assertNotEqual(cached_root, None,
                            msg="Packages were expected to be cached, but were not.")

        # Test that the package is not immediately cached, since it is asynchronous
        # WARNING: This is dangerous since it does open the test to a race condition and
        #   will fail if the cache happens faster than the resolve.
        self.assertNotEqual(resolve_not_always_cached, False)

        expected_payload_file = os.path.join(cached_root, "stuff.txt")
        self.assertTrue(os.path.exists(expected_payload_file))

        # check that refs to root point to cache location in rex code
        for ref in ("resolve.timestamped.root", "'{resolve.timestamped.root}'"):
            proc = c.execute_rex_code(
                code="info(%s)" % ref,
                stdout=subprocess.PIPE,
                universal_newlines=True
            )

            out, _ = proc.communicate()
            root = out.strip()

            self.assertEqual(
                root, cached_root,
                "Reference %r should resolve to %s, but resolves to %s"
                % (ref, cached_root, root)
            )

    @install_dependent()
    def test_caching_on_resolve_synchronous(self):
        """Test that cache is updated as expected on
        resolved env using syncrhonous package caching."""
        pkgcache = self._pkgcache()

        with restore_os_environ():
            # set config settings into env so rez-pkg-cache proc sees them
            os.environ.update(self.get_settings_env())

            # Creating the context will synchronously add variants to the cache
            c = ResolvedContext(
                ["timestamped-1.2.0", "pyfoo-3.1.0"],
                package_cache_async=False,
            )

        variant = c.get_resolved_package("timestamped")
        # The first time we try to access it will be cached, because the cache is blocking
        cached_root = pkgcache.get_cached_root(variant)
        self.assertNotEqual(cached_root, None)

        expected_payload_file = os.path.join(cached_root, "stuff.txt")
        self.assertTrue(os.path.exists(expected_payload_file))

        # check that refs to root point to cache location in rex code
        for ref in ("resolve.timestamped.root", "'{resolve.timestamped.root}'"):
            proc = c.execute_rex_code(
                code="info(%s)" % ref,
                stdout=subprocess.PIPE,
                universal_newlines=True
            )

            out, _ = proc.communicate()
            root = out.strip()

            self.assertEqual(
                root, cached_root,
                "Reference %r should resolve to %s, but resolves to %s"
                % (ref, cached_root, root)
            )
