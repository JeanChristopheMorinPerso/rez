# SPDX-License-Identifier: Apache-2.0
# Copyright Contributors to the Rez Project


filesystem = {
    # The mechanism used to create the lockfile. If set to 'default', this will
    # use hardlinks (link) if the 'os.link' method is present, otherwise mkdir is used.
    # Valid options are 'default', 'mkdir', 'link', or 'symlink'
    "file_lock_type": "default",

    # The timeout to use when creating file locks. This is done when a variant is
    # installed into an existing package, to prevent multiple file writes at
    # once (which could result in a variant install getting lost). The timeout
    # value is in seconds. A value of zero indicates no timeout.
    "file_lock_timeout": 10,

    # The relative directory, under the repository location, where file locks
    # are created. You might need to use this option when file permissions are
    # locked down so that only certain users can release certain packages. In
    # this scenario, package releases may fail because a user with limited
    # permissions will fail to create the lockfile in the repository root. By
    # providing a subdirectory, you can open up the permissions on this
    # directory only. If null, lockfiles are left created in the root.
    #
    # Note: The directory can have any name, but we suggest '.lock' as the
    # standard convention.
    "file_lock_dir": None,

    # If True, verify that a potential package directory contains a package.py /
    # package.yaml file before treating it as a package. There *shouldn't* be
    # non-packages in these directories, and the solver is faster if this value
    # is False, because a lot of file stats are avoided.
    "check_package_definition_files": False,

    # A list of filenames that are expected to contain Rez definitions.
    # The list will be checked in top to bottom order, and the first filename
    # that contains a valid package definition will be used. You might need to
    # use this option if the name 'package.[py/yaml]' is being used by a different
    # packaging system.
    #
    # Please note: The first filename in this list is used as the installed /
    # released package filename, regardless of the definition filename present
    # in the source.
    #
    "package_filenames": [
        "package"
    ]
}
