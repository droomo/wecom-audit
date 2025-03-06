from setuptools import setup, find_packages
import os
import shutil

os.makedirs("build", exist_ok=True)

os.system("cd build && cmake .. && make")

so_file = "build/libwecom_audit.so"
if os.path.exists(so_file):
    os.makedirs("wecom_audit", exist_ok=True)
    target_so = "wecom_audit/libwecom_audit.so"
    if os.path.exists(target_so):
        os.remove(target_so)
    os.symlink(os.path.abspath(so_file), target_so)

if not os.path.exists("wecom_audit/__init__.py"):
    shutil.copy2("wecom_audit/__init__.py", "wecom_audit/")

setup(
    name="wecom-audit",
    version="0.1.0",
    packages=find_packages(include=["wecom_audit", "wecom_audit.*"]),
    python_requires=">=3.11",
    package_data={
        "wecom_audit": ["*.so"],
    },
    include_package_data=True,
)
