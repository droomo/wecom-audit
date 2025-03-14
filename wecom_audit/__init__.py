import json
import ctypes
from ctypes import c_void_p, c_char_p, c_ulonglong, c_bool
from pathlib import Path

LIB_PATH = Path(__file__).parent / "libwecom_audit.so"

lib = ctypes.CDLL(LIB_PATH.as_posix())

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
    def __init__(self, config_path_str):
        config_path = Path(config_path_str)
        with config_path.open('r') as f:
            config = json.load(f)

        private_key_path_str = config.get('private_key_path')

        assert private_key_path_str is not None, "private_key_path is required"
        
        private_key_path = Path(private_key_path_str)

        if not private_key_path.exists() and not private_key_path.is_absolute():
            print(f"private_key_path {private_key_path} does not exist under current directory, using parent directory of config file [{config_path.parent}] instead")
            private_key_path = config_path.parent / private_key_path

        assert private_key_path.exists(), f"private_key_path {private_key_path} does not exist"

        config['private_key_path'] = private_key_path.absolute().as_posix()
        config_json = json.dumps(config)
        
        self.decryptor = lib.create_decryptor()
        if not lib.init_decryptor(self.decryptor, config_json.encode()):
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
