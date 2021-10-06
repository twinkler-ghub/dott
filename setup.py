# vim: set tabstop=4 expandtab :
###############################################################################
#   Copyright (c) 2019-2021 ams AG
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
###############################################################################

# Authors:
# - Thomas Winkler, ams AG, thomas.winkler@ams.com

import glob
import hashlib
import os
import shlex
import shutil
import ssl
import stat
import subprocess
import sys
import urllib.request
import tarfile
import zipfile
from typing import List
from zipfile import ZipFile
from datetime import date

import setuptools
from setuptools import Distribution
from wheel.bdist_wheel import bdist_wheel

build_version = os.environ.get('BUILD_VERSION')
if build_version is None:
    build_version = f'{date.today().strftime("%Y%m%d")}'


class CustomInstallCommand(bdist_wheel):

    script_path = os.path.dirname(os.path.realpath(__file__))
    data_folder_relative = 'dott_data'  # relative to this file
    data_folder = os.path.join(script_path, data_folder_relative)  # destination folder in python distribution
    data_apps_folder = os.path.join(data_folder, 'apps')

    def __init__(self, dist, check_files: bool = True):
        super().__init__(dist)

        mirror_url: str = os.environ.get('DEP_MIRROR_URL')

        self._gdb_url = 'https://developer.arm.com/-/media/Files/downloads/gnu-rm/9-2020q2/gcc-arm-none-eabi-9-2020-q2-update-win32.zip'
        if mirror_url is not None:
            print(f'Using DEP_MIRROR_URL ({mirror_url}) for GCC Windows download...')
            # note: use local mirror (declared in build environment), if available
            self._gdb_url = f'{mirror_url}/gcc-arm-none-eabi-9-2020-q2-update-win32.zip'
        self._gdb_version_info = 'gcc-arm-none-eabi-9-2020-q2-update-win32'
        self._gdb_folder = os.path.join(CustomInstallCommand.data_apps_folder, 'gdb')
        self._gdb_dload_file = 'gdb_win32.zip'
        self._gdb_dload_file_sha256 = '49d6029ecd176deaa437a15b3404f54792079a39f3b23cb46381b0e6fbbe9070'
        self._gdb_dload_file_valid = False

        self._python27_url = 'https://github.com/winpython/winpython/releases/download/1.7.20170401/WinPython-32bit-2.7.13.1Zero.exe'
        if mirror_url is not None:
            # note: use local mirror (declared in build environment), if available
            print(f'Using DEP_MIRROR_URL ({mirror_url}) for Python 2.7 Windows download...')
            self._python27_url = f'{mirror_url}/1.7.20170401/WinPython-32bit-2.7.13.1Zero.exe'
        self._python27_url = 'https://srcint01.amsint.com/dott/download/dep_mirror/WinPython-32bit-2.7.13.1Zero.exe'
        self._python27_version_info = 'WinPython 2.7.13.1, 32bit'
        self._python27_folder = os.path.join(CustomInstallCommand.data_apps_folder, 'python27')
        self._python27_dload_file = 'python27_win32.exe'
        self._python27_dload_file_sha256 = 'ac3d276b18b522547bc04f759c3b7e8bfdf222d8a67b3edd847a800b8e2e1c4c'
        self._python27_dload_file_valid = False

        if check_files:
            self._check_dload_files()  # check if download files already exist and are valid

    def _check_dload_files(self) -> bool:
        if os.path.exists(self._gdb_dload_file):
            f = open(self._gdb_dload_file, "rb")
            data = f.read()
            file_hash = hashlib.sha256(data).hexdigest()
            if self._gdb_dload_file_sha256 == file_hash:
                print(f'{self._gdb_dload_file} exists and has valid checksum')
                self._gdb_dload_file_valid = True
            else:
                print(f'Removing corrupt {self._gdb_dload_file}.')
                os.remove(self._gdb_dload_file)

        if os.path.exists(self._python27_dload_file):
            f = open(self._python27_dload_file, "rb")
            data = f.read()
            file_hash = hashlib.sha256(data).hexdigest()
            f.close()
            if self._python27_dload_file_sha256 == file_hash:
                print(f'{self._python27_dload_file} exists and has valid checksum')
                self._python27_dload_file_valid = True
            else:
                print(f'Removing corrupt {self._python27_dload_file}.')
                os.remove(self._python27_dload_file)

        return self._python27_dload_file_valid and self._gdb_dload_file_valid

    def _print_progress(self, count, block_size, total_size):
        one = total_size / block_size // 100
        if count % one == 0:
            sys.stdout.write('.')
            sys.stdout.flush()

    def _unpack_gcc(self):
        gdb_files = ('arm-none-eabi-gdb-py.exe',
                     'arm-none-eabi-addr2line.exe',
                     'arm-none-eabi-gcov.exe',
                     'arm-none-eabi-objcopy.exe',
                     'arm-none-eabi-strip.exe',
                     'arm-none-eabi-elfedit.exe',
                     'arm-none-eabi-objdump.exe',
                     'arm-none-eabi-gcov-dump.exe',
                     'arm-none-eabi-readelf.exe',
                     'arm-none-eabi-gcov-tool.exe',
                     'arm-none-eabi-nm.exe',
                     'arm-none-eabi-strings.exe',
                     'license.txt',
                     'release.txt',
                     'readme.txt')

        with ZipFile(self._gdb_dload_file, 'r') as zipObj:
            file_names = zipObj.namelist()
            for file_name in file_names:
                if file_name.endswith('.py'):
                    zipObj.extract(file_name, self._gdb_folder)
                else:
                    for gdb_file in gdb_files:
                        if file_name.endswith(gdb_file):
                            zipObj.extract(file_name, self._gdb_folder)

        with open(os.path.join(self._gdb_folder, 'version.txt'), 'w+') as f:
            f.write(f'GDB and support tools extracted from GNU Arm Embedded Toolchain.\n')
            f.write(f'version: {self._gdb_version_info}\n')
            f.write(f'downloaded from: {self._gdb_url}\n')
            f.write(f'Note: To save space only selected parts of the full package have been included.\n'
                    f'      No other modifications have been performed.\n'
                    f'      The license of GDB can be found in share/doc/gcc-arm-none-eabi/license.txt\n')

    def _unpack_python27(self):
        inst_path = self._python27_folder.replace('\\', '\\\\').replace('/', '\\\\')

        # unpack WinPython
        args = shlex.split(f'{self._python27_dload_file} /S /D={inst_path}')
        proc = subprocess.Popen(args)
        proc.wait()

        with open(os.path.join(self._python27_folder, 'version.txt'), 'w+') as f:
            f.write(f'WinPython 2.7 Environment for GDB\n')
            f.write(f'version: {self._python27_version_info}\n')
            f.write(f'downloaded from: {self._python27_url}\n')
            f.write(f'Note: This WinPython 2.7.13.1 environment is required for the GNU Arm Embedded GDB.\n'
                    f'      No modifications have been performed.\n'
                    f'      The license of Python 2.7 can be found in python-2.7.13/LICENSE.txt')

    def _write_version(self):
        global build_version
        with open(os.path.join(CustomInstallCommand.data_apps_folder, 'version.txt'), 'w+') as f:
            f.write(f'DOTT runtime apps\n')
            f.write(f'version: {build_version}\n')

    def run(self):
        # dependency fetching
        print('Fetching dependencies...')
        print('  GNU Arm Embedded providing GDB for Arm Cortex-M', end='')
        sys.stdout.flush()

        if not self._gdb_dload_file_valid:
            with urllib.request.urlopen(self._gdb_url, context=ssl.SSLContext()) as u, open (self._gdb_dload_file, 'wb') as f:
                f.write(u.read())


        print(' [done]')
        print('  Python 2.7 library for GDB', end='')
        sys.stdout.flush()
        if not self._python27_dload_file_valid:
            with urllib.request.urlopen(self._python27_url, context=ssl.SSLContext()) as u, open (self._python27_dload_file, 'wb') as f:
                f.write(u.read())
        print(' [done]')

        if not self._check_dload_files():
            print("Downloaded files could not be verified (checksums don't match)")
            sys.exit(-1)

        # dependency unpacking
        print('Unpacking dependencies...')
        print('  Unpacking GDB from GNU Arm Embedded Toolchain...', end='')
        sys.stdout.flush()
        self._unpack_gcc()
        print('  [done]')
        print('  Unpacking Python 2.7 library for GDB...', end='')
        sys.stdout.flush()
        self._unpack_python27()
        print('  [done]')

        # write runtime apps version
        self._write_version()

        # we are done with unpacking. now we can set the correct data_files (in setup() this is too early)
        self.distribution.data_files = self._get_package_data_files()
        super().run()

    def finalize_options(self):
        super().finalize_options()
        #self.root_is_pure = False
        self.plat_name_supplied=True
        self.plat_name='win_amd64'

    def _get_package_data_files(self) -> List:
        ret = []
        for root, dirs, files in os.walk(CustomInstallCommand.data_folder_relative):
            src_files = []
            root = root.replace('\\', '/')
            root = root.replace('\\\\', '/')
            for f in files:
                f = f.replace('\\', '/')
                f = f.replace('\\\\', '/')
                src_files.append(root + '/' + f)
            ret.append((root, src_files))

        return ret


class CustomInstallCommandLinuxAmd64(CustomInstallCommand):

    def __init__(self, dist):
        super().__init__(dist, check_files=False)

        mirror_url: str = os.environ.get('DEP_MIRROR_URL')

        self._gdb_url = 'https://developer.arm.com/-/media/Files/downloads/gnu-rm/9-2020q2/gcc-arm-none-eabi-9-2020-q2-update-x86_64-linux.tar.bz2'
        if mirror_url is not None:
            # note: use local mirror to avoid sporadic download issues
            print(f'Using DEP_MIRROR_URL ({mirror_url}) for GCC Linux download...')
            self._gdb_url = 'https://srcint01.amsint.com/dott/download/dep_mirror/gcc-arm-none-eabi-9-2020-q2-update-x86_64-linux.tar.bz2'
        self._gdb_version_info = 'gcc-arm-none-eabi-9-2020-q2-update-x86_64-linux'
        self._gdb_folder = os.path.join(CustomInstallCommandLinuxAmd64.data_apps_folder, 'gdb')
        self._gdb_dload_file = 'gdb_linux_amd64.tar.bz2'
        self._gdb_dload_file_sha256 = '5adc2ee03904571c2de79d5cfc0f7fe2a5c5f54f44da5b645c17ee57b217f11f'
        self._gdb_dload_file_valid = False

        self._python27_url = 'http://de.archive.ubuntu.com/ubuntu/pool/universe/p/python2.7/libpython2.7_2.7.18~rc1-2_amd64.deb'
        # note: use local mirror to avoid sporadic download issues
        if mirror_url is not None:
            # note: use local mirror to avoid sporadic download issues
            print(f'Using DEP_MIRROR_URL ({mirror_url}) for Python 2.7 Linux download...')
            self._python27_url = 'https://srcint01.amsint.com/dott/download/dep_mirror/libpython2.7_2.7.18~rc1-2_amd64.deb'
        self._python27_version_info = 'libpython2.7.18~rc1-2, 64bit'
        self._python27_folder = os.path.join(CustomInstallCommandLinuxAmd64.data_apps_folder, 'python27')
        self._python27_dload_file = 'python27_linux_amd64.deb'
        self._python27_dload_file_sha256 = '77d67e841b4812bdc32274219cc86c316d357c00e8589d54be9987cb060db832'
        self._python27_dload_file_valid = False

        self._check_dload_files()  # check if download files already exist and are valid

    def _unpack_gcc(self):
        gdb_files = ('arm-none-eabi-gdb-py',
                     'arm-none-eabi-addr2line',
                     'arm-none-eabi-gcov',
                     'arm-none-eabi-objcopy',
                     'arm-none-eabi-strip',
                     'arm-none-eabi-elfedit',
                     'arm-none-eabi-objdump',
                     'arm-none-eabi-gcov-dump',
                     'arm-none-eabi-readelf',
                     'arm-none-eabi-gcov-tool',
                     'arm-none-eabi-nm',
                     'arm-none-eabi-strings',
                     'license.txt',
                     'release.txt',
                     'readme.txt')

        tar = tarfile.open(self._gdb_dload_file, 'r:bz2')
        first_dir: str = tar.getmembers()[0].name.split('/')[0]
        gdb_folder_tmp = f'{self._gdb_folder}_tmp'

        for file_name in tar:
            if file_name.name.endswith('.py'):
                tar.extract(file_name, gdb_folder_tmp)
            else:
                for gdb_file in gdb_files:
                    if file_name.name.endswith(gdb_file):
                        tar.extract(file_name, gdb_folder_tmp)

        shutil.move(os.path.join(gdb_folder_tmp, first_dir), self._gdb_folder)
        shutil.rmtree(gdb_folder_tmp)

        with open(os.path.join(self._gdb_folder, 'version.txt'), 'w+') as f:
            f.write(f'GDB and support tools extracted from GNU Arm Embedded Toolchain.\n')
            f.write(f'version: {self._gdb_version_info}\n')
            f.write(f'downloaded from: {self._gdb_url}\n')
            f.write(f'Note: To save space only selected parts of the full package have been included.\n'
                    f'      No other modifications have been performed.\n'
                    f'      The license of GDB can be found in share/doc/gcc-arm-none-eabi/license.txt\n')

    def _unpack_python27(self):
        pass
        # On Ubuntu 20.04 install Python2.7 (lib) and NCurses 5 (lib) to satisfy gdb's dependencies.
        # sudo apt-get install libpython2.7 libncurses5 python-is-python3

    def finalize_options(self):
        super().finalize_options()
        #self.root_is_pure = False
        self.plat_name_supplied=True
        self.plat_name='manylinux2014_x86_64'


def _set_execperms_in_whl(dir: str, pattern: str):
    for name in glob.glob(os.path.join(dir, '*.whl')):
        name_tmp: str = name.replace('.whl', '_NEW.whl')

        # create temp file
        with open(name_tmp, 'w') as f:
            f.close()

        # open input and output whl (zip) files; set files matching pattern executable in output archive.
        zf_in = zipfile.ZipFile(name, 'r')
        zf_out = zipfile.ZipFile(name_tmp, 'w')
        zf_out.comment = zf_in.comment
        for item in zf_in.filelist:
            if pattern in item.filename:
                perm = item.external_attr >> 16 | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
                item.external_attr = perm << 16
            zf_out.writestr(item, zf_in.read(item.filename))
        zf_out.close()
        zf_in.close()

        # remove the original whl and replace it with the new one
        os.remove(name)
        shutil.move(name_tmp, name)


# ----------------------------------------------------------------------------------------------------------------------
shared_classifiers = [
                  "Environment :: Console",
                  "License :: OSI Approved :: Apache Software License",
                  "Topic :: Software Development :: Testing",
                  "Topic :: Software Development :: Debuggers",
                  "Topic :: Software Development :: Embedded Systems"
              ]

shared_author_email = "thomas.winkler@ams.com"

shared_author = "Thomas Winkler"

shared_url = "https://github.com/twinkler-ams-osram/dott"

shared_install_requires = [
                       "ams-dott-runtime",
                       "pygdbmi==0.10.0.1",
                       "pylink-square==0.11.1",
                       "pytest",
                       "pytest-cov",
                       "pytest-instafail",
                       "pytest-repeat"
                   ]

def setup_dott_runtime():
    setuptools.setup(
        cmdclass={
            'bdist_wheel': CustomInstallCommand,
        },
        name="ams-dott-runtime",
        version=build_version,
        author=shared_author,
        author_email=shared_author_email,
        description="Runtime Environment for Debugger-based on Target Testing (DOTT)",
        long_description="",
        long_description_content_type="text/markdown",
        url=shared_url,
        packages=[],
        data_files=[],
        platforms=['nt'],
        include_package_data=True,
        classifiers=shared_classifiers,
        install_requires=[
        ],
        python_requires='>=3.6',
    )


def setup_dott_runtime_linux_amd64():
    setuptools.setup(
        cmdclass={
            'bdist_wheel': CustomInstallCommandLinuxAmd64,
        },
        name="ams-dott-runtime",
        version=build_version,
        author=shared_author,
        author_email=shared_author_email,
        description="Runtime Environment for Debugger-based on Target Testing (DOTT)",
        long_description="",
        long_description_content_type="text/markdown",
        url=shared_url,
        packages=[],
        data_files=[],
        platforms=['Linux'],
        include_package_data=True,
        shared_classifiers=shared_classifiers,
        install_requires=shared_install_requires,
        python_requires='>=3.6',
    )


def setup_dott():
    setuptools.setup(
        cmdclass={
        },
        name="ams-dott",
        version=build_version,
        author=shared_author,
        author_email=shared_author_email,
        description="Debugger-based on Target Testing (DOTT)",
        long_description="",
        long_description_content_type="text/markdown",
        url=shared_url,
        packages=['dottmi'],
        data_files=[],  # data_files are set in bdist_wheel.run (in setup() this is too early)
        platforms=[],
        include_package_data=False,
        classifiers=shared_classifiers,
        install_requires=shared_install_requires,
        python_requires='>=3.6',
    )


# cleanup folders
shutil.rmtree(CustomInstallCommand.data_folder_relative, ignore_errors=True)

if '--dott-runtime-win-amd64' in sys.argv:
    sys.argv.remove('--dott-runtime-win-amd64')
    setup_dott_runtime()
elif '--dott-runtime-linux-amd64' in sys.argv:
    sys.argv.remove('--dott-runtime-linux-amd64')
    setup_dott_runtime_linux_amd64()
    _set_execperms_in_whl(os.path.join(os.path.dirname(__file__), 'dist'), '/bin/')
else:
    setup_dott()
