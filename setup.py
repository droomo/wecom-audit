from setuptools import setup, find_packages, Extension
from setuptools.command.build_ext import build_ext
import os
import sys
import subprocess
import shutil
import urllib.request
import tarfile
import tempfile

class CMakeExtension(Extension):
    def __init__(self, name, sourcedir=""):
        Extension.__init__(self, name, sources=[])
        self.sourcedir = os.path.abspath(sourcedir)

class CMakeBuild(build_ext):
    def run(self):
        # Check for CMake
        try:
            subprocess.check_output(["cmake", "--version"])
        except OSError:
            raise RuntimeError("CMake must be installed to build the extension")
            
        # Check for OpenSSL
        try:
            subprocess.check_output(["pkg-config", "--exists", "openssl"])
        except OSError:
            raise RuntimeError("OpenSSL development files must be installed")
        
        # Ensure C_sdk directory exists
        self._ensure_c_sdk_exists()
            
        for ext in self.extensions:
            self.build_extension(ext)
    
    def _ensure_c_sdk_exists(self):
        c_sdk_dir = os.path.join(os.path.abspath('.'), "C_sdk")
        if not os.path.exists(c_sdk_dir) or not os.path.exists(os.path.join(c_sdk_dir, "WeWorkFinanceSdk_C.h")):
            print("C_sdk directory not found or incomplete. Downloading SDK...")
            os.makedirs(c_sdk_dir, exist_ok=True)
            
            # SDK URL - replace with the actual URL if different
            sdk_url = "https://jiexiang.oss-cn-wulanchabu.aliyuncs.com/misc/%E6%83%A0%E5%B7%A5%E4%BA%91/sdk_x86_v3_20250205.tgz"
            
            # Download and extract SDK
            with tempfile.NamedTemporaryFile(suffix=".tgz", delete=False) as tmp_file:
                print(f"Downloading SDK from {sdk_url}...")
                urllib.request.urlretrieve(sdk_url, tmp_file.name)
                
                print(f"Extracting SDK to {c_sdk_dir}...")
                with tarfile.open(tmp_file.name, "r:gz") as tar:
                    # Extract only the necessary files
                    for member in tar.getmembers():
                        if member.name.endswith(("WeWorkFinanceSdk_C.h", "libWeWorkFinanceSdk_C.so")):
                            member.name = os.path.basename(member.name)
                            tar.extract(member, c_sdk_dir)
                
                os.unlink(tmp_file.name)
            
            print("SDK downloaded and extracted successfully.")

    def build_extension(self, ext):
        extdir = os.path.abspath(os.path.dirname(self.get_ext_fullpath(ext.name)))
        
        if not os.path.exists(self.build_temp):
            os.makedirs(self.build_temp)
            
        # Configure and build
        subprocess.check_call(
            ["cmake", ext.sourcedir], 
            cwd=self.build_temp
        )
        subprocess.check_call(
            ["cmake", "--build", "."], 
            cwd=self.build_temp
        )
        
        # Copy the library to the package directory
        lib_file = os.path.join(self.build_temp, "libwecom_audit.so")
        if os.path.exists(lib_file):
            os.makedirs(os.path.dirname(self.get_ext_fullpath(ext.name)), exist_ok=True)
            target_so = os.path.join(extdir, "libwecom_audit.so")
            if os.path.exists(target_so):
                os.remove(target_so)
            shutil.copy2(lib_file, target_so)
            
        # Copy C_sdk dependencies
        c_sdk_dir = os.path.join(ext.sourcedir, "C_sdk")
        if os.path.exists(c_sdk_dir):
            target_sdk_dir = os.path.join(extdir, "C_sdk")
            os.makedirs(target_sdk_dir, exist_ok=True)
            
            # Copy WeWork SDK library
            sdk_lib = os.path.join(c_sdk_dir, "libWeWorkFinanceSdk_C.so")
            sdk_header = os.path.join(c_sdk_dir, "WeWorkFinanceSdk_C.h")
            
            if os.path.exists(sdk_lib):
                shutil.copy2(sdk_lib, os.path.join(target_sdk_dir, "libWeWorkFinanceSdk_C.so"))
            
            if os.path.exists(sdk_header):
                shutil.copy2(sdk_header, os.path.join(target_sdk_dir, "WeWorkFinanceSdk_C.h"))

# Custom install command to ensure C_sdk is included
from setuptools.command.install import install
class CustomInstall(install):
    def run(self):
        install.run(self)

setup(
    name="wecom-audit",
    version="0.1.1",
    packages=find_packages(include=["wecom_audit", "wecom_audit.*"]),
    python_requires=">=3.11",
    ext_modules=[CMakeExtension("wecom_audit.libwecom_audit")],
    cmdclass={
        "build_ext": CMakeBuild,
        "install": CustomInstall,
    },
    package_data={
        "wecom_audit": ["*.so", "C_sdk/*.so", "C_sdk/*.h"],
    },
    include_package_data=True,
    setup_requires=["setuptools>=42", "wheel"],
    install_requires=[],
)
