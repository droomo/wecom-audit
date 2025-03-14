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
            
            # Use local SDK file if available
            local_sdk_path = os.path.join(os.path.abspath('.'), "sdk_x86_v3_20250205.tgz")
            
            if os.path.exists(local_sdk_path):
                print(f"Using local SDK file: {local_sdk_path}")
                sdk_file = local_sdk_path
            else:
                # SDK URL - replace with the actual URL if different
                sdk_url = "https://jiexiang.oss-cn-wulanchabu.aliyuncs.com/misc/%E6%83%A0%E5%B7%A5%E4%BA%91/sdk_x86_v3_20250205.tgz"
                
                # Download SDK
                with tempfile.NamedTemporaryFile(suffix=".tgz", delete=False) as tmp_file:
                    print(f"Downloading SDK from {sdk_url}...")
                    urllib.request.urlretrieve(sdk_url, tmp_file.name)
                    sdk_file = tmp_file.name
            
            # Extract SDK
            print(f"Extracting SDK to {c_sdk_dir}...")
            with tarfile.open(sdk_file, "r:gz") as tar:
                # Extract only the necessary files
                for member in tar.getmembers():
                    if member.name.endswith(("WeWorkFinanceSdk_C.h", "libWeWorkFinanceSdk_C.so")):
                        member.name = os.path.basename(member.name)
                        tar.extract(member, c_sdk_dir)
            
            # Clean up temporary file if we downloaded it
            if sdk_file != local_sdk_path and os.path.exists(sdk_file):
                os.unlink(sdk_file)
                
            print("SDK extracted successfully.")

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

# Custom bdist_wheel command to ensure proper wheel building
from wheel.bdist_wheel import bdist_wheel

class BdistWheelCustom(bdist_wheel):
    def finalize_options(self):
        bdist_wheel.finalize_options(self)
        # Mark the wheel as platform-specific (not pure Python)
        self.root_is_pure = False
        # Set the platform tag to manylinux2014 for compatibility with PyPI
        self.plat_name_supplied = True
        if self.plat_name.startswith('linux'):
            self.plat_name = 'manylinux2014_x86_64'

# read README.md as long description
try:
    with open("README.md", "r", encoding="utf-8") as fh:
        long_description = fh.read()
except FileNotFoundError:
    long_description = "WeChat Work (WeCom) Audit API Python Wrapper"

setup(
    name="wecom-audit",
    version="0.1.2",
    packages=find_packages(include=["wecom_audit", "wecom_audit.*"]),
    python_requires=">=3.11",
    ext_modules=[CMakeExtension("wecom_audit.libwecom_audit")],
    cmdclass={
        "build_ext": CMakeBuild,
        "bdist_wheel": BdistWheelCustom,
    },
    package_data={
        "wecom_audit": ["*.so", "C_sdk/*.so", "C_sdk/*.h"],
    },
    include_package_data=True,
    setup_requires=["setuptools>=42", "wheel"],
    install_requires=[],
    author="droomo, Grainstone",
    author_email="th@droomo.com",
    description="Python wrapper for WeChat Work (WeCom) Audit API. © 2025 puyuan.tech, Ltd. All rights reserved.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords="wecom, wechat work, audit, 企业微信, 企微, 消息获取, 会话存档, puyuan.tech",
    url="https://github.com/droomo/wecom-audit",
    project_urls={
        "Bug Tracker": "https://github.com/droomo/wecom-audit/issues",
        "Source Code": "https://github.com/droomo/wecom-audit",
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Operating System :: POSIX :: Linux",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    zip_safe=False,
)
