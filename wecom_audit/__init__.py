import ctypes
from ctypes import c_void_p, c_char_p, c_ulonglong, c_bool
import json
import os

# 获取当前文件所在目录
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# 构建库文件的完整路径
LIB_PATH = os.path.join(os.path.dirname(CURRENT_DIR), "build", "libwecom_audit.so")

# 加载库
lib = ctypes.CDLL(LIB_PATH)

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
        # 读取配置文件
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # 将私钥路径转换为绝对路径
        private_key_path = config.get('private_key_path', 'key/private.pem')
        if not os.path.isabs(private_key_path):
            private_key_path = os.path.join(os.path.dirname(config_path), private_key_path)
        
        # 更新配置文件中的私钥路径
        config['private_key_path'] = private_key_path
        
        # 创建临时配置文件
        temp_config = os.path.join(os.path.dirname(config_path), 'temp_config.json')
        with open(temp_config, 'w') as f:
            json.dump(config, f)
        
        self.decryptor = lib.create_decryptor()
        if not lib.init_decryptor(self.decryptor, temp_config.encode()):
            raise RuntimeError("Failed to initialize decryptor")
        
        # 清理临时配置文件
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

if __name__ == "__main__":
    audit = WeComAudit("config.json")
    messages = audit.get_new_messages(7)
    print(json.dumps(messages, indent=2))

    with open("messages.json", "w") as f:
        json.dump(messages, f, indent=2, ensure_ascii=False)
