#pragma once
#include <string>

#define EXPORT __attribute__((visibility("default")))

extern "C" {
    EXPORT void* create_decryptor();
    
    EXPORT bool init_decryptor(void* decryptor, const char* config_path);
    
    EXPORT const char* get_new_messages(void* decryptor, unsigned long long seq);
    
    EXPORT void destroy_decryptor(void* decryptor);
    
    EXPORT void free_string(char* str);
} 