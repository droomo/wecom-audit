#pragma once
#include <string>

#ifdef _WIN32
    #define EXPORT __declspec(dllexport)
#else
    #define EXPORT __attribute__((visibility("default")))
#endif

extern "C" {
    // 创建解密器实例
    EXPORT void* create_decryptor();
    
    // 初始化解密器
    EXPORT bool init_decryptor(void* decryptor, const char* config_path);
    
    // 获取新消息
    EXPORT const char* get_new_messages(void* decryptor, unsigned long long seq);
    
    // 释放解密器
    EXPORT void destroy_decryptor(void* decryptor);
    
    // 释放字符串内存
    EXPORT void free_string(char* str);
} 