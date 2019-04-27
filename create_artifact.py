import os
import sys
import gzip
import errno
import shutil
import tarfile
import tempfile
import subprocess


temp_dir = tempfile.mkdtemp(suffix="_rez_source")

print "Copying source code into {0!r}".format(temp_dir)
for root, dirs, files in os.walk("src"):
    if root.startswith("src/support"):
        continue

    for file_ in files:
        file_path_src = os.path.join(root, file_)
        file_path_dest = os.path.join(
            temp_dir,
            os.path.sep.join(file_path_src.split(os.path.sep)[1:])  # Strip src/
        )

        try:
            os.makedirs(os.path.dirname(file_path_dest))
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise
            pass

        shutil.copy2(file_path_src, file_path_dest)

vendor_dir = os.path.join(temp_dir, "rez", "vendor")
print "Installing Rez dependencies into {0!r}".format(vendor_dir)

subprocess.check_call(
    [
        "python2",
        "-m",
        "pip",
        "install",
        "-r",
        "requirements.txt",
        "--target",
        vendor_dir,
        "--no-deps"
    ]
)


sys.path.insert(0, "src")

from rez import __version__

tar_base_name = "rez-{0}".format(__version__)
tar_name = "{0}.tar.gz".format(tar_base_name)

temp_dir_gz = tempfile.mkdtemp(suffix="_rez_gz")
gz = gzip.GzipFile(os.path.join(temp_dir_gz, tar_name), mode="wb")


with tarfile.TarFile(
    os.path.join(temp_dir_gz, tar_name),
    mode="w",
    fileobj=gz,
    format=tarfile.PAX_FORMAT,
) as tar:
    for root, dirs, files in os.walk(temp_dir):
        for f in files:
            if f.endswith(".pyc") or f.endswith(".so"):
                continue

            path = os.path.join(os.path.realpath(root), f)

            relpath = os.path.relpath(
                path, os.path.realpath(temp_dir)
            )

            tar_info = tar.gettarinfo(str(path), arcname=relpath)

            if tar_info.isreg():
                with open(path, "rb") as f:
                    tar.addfile(tar_info, f)
            else:
                tar.addfile(tar_info)  # Symlinks & ?

gz.close()
print "Final artifact: {0!r}".format(os.path.join(temp_dir_gz, tar_name))
