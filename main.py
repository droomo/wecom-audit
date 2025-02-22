import ctypes
from ctypes import c_void_p, c_char_p, c_ulonglong, c_bool
import json

# 加载库
lib = ctypes.CDLL('./build/libwecom_audit.so')

# 设置函数参数和返回类型
lib.create_decryptor.restype = c_void_p
lib.init_decryptor.argtypes = [c_void_p, c_char_p]
lib.init_decryptor.restype = c_bool
lib.get_new_messages.argtypes = [c_void_p, c_ulonglong]
lib.get_new_messages.restype = c_char_p
lib.destroy_decryptor.argtypes = [c_void_p]
lib.free_string.argtypes = [c_char_p]

class WeComAudit:
    def __init__(self, config_path):
        self.decryptor = lib.create_decryptor()
        if not lib.init_decryptor(self.decryptor, config_path.encode()):
            raise RuntimeError("Failed to initialize decryptor")

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

if __name__ == "__main__":
    audit = WeComAudit("config.json")
    messages = audit.get_new_messages(7)
    print(json.dumps(messages, indent=2))

    with open("messages.json", "w") as f:
        json.dump(messages, f, indent=2, ensure_ascii=False)
