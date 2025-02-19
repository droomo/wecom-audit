cmake_minimum_required(VERSION 3.10)
project(WeWorkFinanceSDK)

# 设置 C++ 标准
set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# 查找 OpenSSL
find_package(OpenSSL REQUIRED)

# 添加头文件目录
include_directories(${CMAKE_SOURCE_DIR}/C_sdk ${OPENSSL_INCLUDE_DIR})

# 设置运行时动态库搜索路径为当前目录
set(CMAKE_INSTALL_RPATH "${CMAKE_SOURCE_DIR}")
set(CMAKE_BUILD_WITH_INSTALL_RPATH TRUE)

# 添加可执行文件
add_executable(we_audit_sdk main.cc)

# 链接 WeWork Finance SDK 库
find_library(WEWORK_LIB WeWorkFinanceSdk_C ${CMAKE_SOURCE_DIR})
if(NOT WEWORK_LIB)
    message(FATAL_ERROR "WeWorkFinanceSdk_C library not found! Please put libWeWorkFinanceSdk_C.so in project root directory.")
endif()

# 链接 WeWork Finance SDK 和 OpenSSL 库
target_link_libraries(we_audit_sdk 
    ${WEWORK_LIB}
    OpenSSL::SSL 
    OpenSSL::Crypto
)
