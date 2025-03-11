cmake_minimum_required(VERSION 3.10)
project(WeWorkFinanceSDK)

# 设置 C++ 标准
set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# 设置生成动态库
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# 查找 OpenSSL
find_package(OpenSSL REQUIRED)

# 添加头文件目录
include_directories(${CMAKE_SOURCE_DIR}/C_sdk ${OPENSSL_INCLUDE_DIR})

# 设置运行时动态库搜索路径
set(CMAKE_INSTALL_RPATH "${CMAKE_SOURCE_DIR}/C_sdk")
set(CMAKE_BUILD_WITH_INSTALL_RPATH TRUE)

# 更新 libWeWorkFinanceSdk_C.so 的路径
link_directories(${CMAKE_SOURCE_DIR}/C_sdk)

# 检查 C_sdk 目录是否存在
if(NOT EXISTS "${CMAKE_SOURCE_DIR}/C_sdk/WeWorkFinanceSdk_C.h")
    message(FATAL_ERROR "C_sdk directory is missing or incomplete. Please run setup.py to download the SDK.")
endif()

# 创建共享库
add_library(wecom_audit SHARED main.cc)

# 链接依赖库
target_link_libraries(wecom_audit 
    -L${CMAKE_SOURCE_DIR}/C_sdk -lWeWorkFinanceSdk_C
    OpenSSL::SSL 
    OpenSSL::Crypto
)

# 创建可执行文件
add_executable(wecom_audit_cli main.cc)

# 链接可执行文件的依赖库
target_link_libraries(wecom_audit_cli
    -L${CMAKE_SOURCE_DIR}/C_sdk -lWeWorkFinanceSdk_C
    OpenSSL::SSL 
    OpenSSL::Crypto
)

# 设置可执行文件的编译选项
set_target_properties(wecom_audit_cli PROPERTIES
    COMPILE_DEFINITIONS "MAIN_PROGRAM"
)
