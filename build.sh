#!/bin/bash

# 创建构建目录
mkdir -p build
cd build

# 运行 CMake 配置
cmake ..

# 编译
make

# 回到项目根目录
cd ..

# 复制可执行文件到根目录
cp build/we_audit_sdk .

# 设置运行时库路径
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$(pwd)

echo "Build completed!" 