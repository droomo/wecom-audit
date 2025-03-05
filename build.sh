#!/bin/bash

# 创建构建目录
mkdir -p build
cd build

# 运行 CMake 配置
cmake ..

# 编译
make && echo "Build completed!" 

# # 设置运行时库路径
# export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$(pwd)
