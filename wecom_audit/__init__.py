import ctypes
from ctypes import c_void_p, c_char_p, c_ulonglong, c_bool
import json
import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
LIB_PATH = os.path.join(CURRENT_DIR, "libwecom_audit.so")

# Add C_sdk directory to LD_LIBRARY_PATH
C_SDK_DIR = os.path.join(CURRENT_DIR, "C_sdk")
if os.path.exists(C_SDK_DIR):
    # Set RPATH for the shared library
    os.environ["LD_LIBRARY_PATH"] = C_SDK_DIR + ":" + os.environ.get("LD_LIBRARY_PATH", "")

try:
    lib = ctypes.CDLL(LIB_PATH)
except OSError as e:
    # Try to load with explicit dependency path
    try:
        sdk_lib_path = os.path.join(C_SDK_DIR, "libWeWorkFinanceSdk_C.so")
        if os.path.exists(sdk_lib_path):
            # Load the dependency first
            ctypes.CDLL(sdk_lib_path)
        # Now try loading our library again
        lib = ctypes.CDLL(LIB_PATH)
    except OSError as e2:
        print(f"Failed to load library from {LIB_PATH}: {e2}")
        print(f"Original error: {e}")
        raise

lib.create_decryptor.restype = c_void_p
lib.init_decryptor.argtypes = [c_void_p, c_char_p]
lib.init_decryptor.restype = c_bool
lib.get_new_messages.argtypes = [c_void_p, c_ulonglong]
lib.get_new_messages.restype = c_char_p
lib.destroy_decryptor.argtypes = [c_void_p]
lib.free_string.argtypes = [c_char_p]
lib.download_file.argtypes = [c_void_p, c_char_p, c_char_p]
lib.download_file.restype = c_bool

class WeComAudit:
    def __init__(self, config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        private_key_path = config.get('private_key_path', 'key/private.pem')
        if not os.path.isabs(private_key_path):
            private_key_path = os.path.join(os.path.dirname(config_path), private_key_path)
        
        config['private_key_path'] = private_key_path
        
        temp_config = os.path.join(os.path.dirname(config_path), 'temp_config.json')
        with open(temp_config, 'w') as f:
            json.dump(config, f)
        
        self.decryptor = lib.create_decryptor()
        if not lib.init_decryptor(self.decryptor, temp_config.encode()):
            raise RuntimeError("Failed to initialize decryptor")
        
        os.remove(temp_config)

    def get_new_messages(self, seq):
        result = lib.get_new_messages(self.decryptor, seq)
        if result:
            json_str = result.decode()
            data = json.loads(json_str)
            if data.get("errcode", 0) != 0:
                raise RuntimeError(f"Failed to get messages: {data.get('errmsg', 'Unknown error')}")
            return data
        return None

    def __del__(self):
        if hasattr(self, 'decryptor'):
            lib.destroy_decryptor(self.decryptor)

    def download_file(self, msg, save_dir):
        json_str = json.dumps(msg)
        result = lib.download_file(self.decryptor, json_str.encode(), save_dir.encode())
        return result

if __name__ == "__main__":
    audit = WeComAudit("config.json")
    messages = audit.get_new_messages(7)
    print(json.dumps(messages, indent=2))

    with open("messages.json", "w") as f:
        json.dump(messages, f, indent=2, ensure_ascii=False)
