#include "WeWorkFinanceSdk_C.h"
#include <stdio.h>
#include <stdlib.h>
#include <string>
#include <openssl/rsa.h>
#include <openssl/pem.h>
#include <openssl/err.h>
#include <openssl/bio.h>
#include <nlohmann/json.hpp>
#include <vector>

using std::string;
using json = nlohmann::json;

class WeWorkFinanceDecryptor {
private:
	WeWorkFinanceSdk_t* sdk;
	const char* private_key;
	string app_id;
	string app_secret;

	string rsa_decrypt(const string& encrypted_data) {
		string decrypted;
		BIO* keybio = BIO_new_mem_buf(private_key, -1);
		RSA* rsa = NULL;
		rsa = PEM_read_bio_RSAPrivateKey(keybio, &rsa, NULL, NULL);
		if (!rsa) {
			printf("Failed to load private key\n");
			BIO_free_all(keybio);
			return "";
		}

		// Base64 decode first
		BIO* b64 = BIO_new(BIO_f_base64());
		BIO* bmem = BIO_new_mem_buf(encrypted_data.c_str(), encrypted_data.length());
		bmem = BIO_push(b64, bmem);
		BIO_set_flags(bmem, BIO_FLAGS_BASE64_NO_NL);
		
		std::vector<unsigned char> buffer(encrypted_data.length());
		int decoded_size = BIO_read(bmem, buffer.data(), encrypted_data.length());
		BIO_free_all(bmem);

		if (decoded_size <= 0) {
			printf("Base64 decode failed\n");
			RSA_free(rsa);
			BIO_free_all(keybio);
			return "";
		}

		// RSA decrypt
		std::vector<unsigned char> decrypted_buf(RSA_size(rsa));
		int result = RSA_private_decrypt(decoded_size, buffer.data(), 
									   decrypted_buf.data(), rsa, RSA_PKCS1_PADDING);
		
		if (result == -1) {
			printf("RSA decrypt failed\n");
			RSA_free(rsa);
			BIO_free_all(keybio);
			return "";
		}

		decrypted = string((char*)decrypted_buf.data(), result);
		RSA_free(rsa);
		BIO_free_all(keybio);
		return decrypted;
	}

	json decrypt_single_message(const json& msg) {
		string encrypt_random_key = msg["encrypt_random_key"];
		string encrypt_chat_msg = msg["encrypt_chat_msg"];
		
		// 保存原始字段
		json original_fields = {
			{"seq", msg["seq"]},
			{"msgid", msg["msgid"]}
		};
		
		// Decrypt random key
		string decrypted_key = rsa_decrypt(encrypt_random_key);
		if (decrypted_key.empty()) {
			printf("Failed to decrypt random key\n");
			return json();
		}

		// Decrypt message
		Slice_t* decrypted_msg = NewSlice();
		int ret = DecryptData(decrypted_key.c_str(), encrypt_chat_msg.c_str(), decrypted_msg);
		if (ret != 0) {
			printf("Failed to decrypt message, ret: %d\n", ret);
			FreeSlice(decrypted_msg);
			return json();
		}

		json decrypted_json = json::parse(GetContentFromSlice(decrypted_msg));
		json complete_msg = original_fields;
		complete_msg["decrypted_content"] = decrypted_json;

		FreeSlice(decrypted_msg);
		return complete_msg;
	}

public:
	WeWorkFinanceDecryptor() : sdk(nullptr), private_key(nullptr) {}
	
	~WeWorkFinanceDecryptor() {
		if (sdk) {
			DestroySdk(sdk);
		}
	}

	bool init(const string& pri_key_path, const string& app_secret_path) {
		// Read private key
		FILE* fp = fopen(pri_key_path.c_str(), "r");
		if (!fp) {
			printf("Can not open private key file %s\n", pri_key_path.c_str());
			return false;
		}

		fseek(fp, 0, SEEK_END);
		long file_size = ftell(fp);
		fseek(fp, 0, SEEK_SET);

		char* pri_key_buf = (char*)malloc(file_size + 1);
		size_t read_size = fread(pri_key_buf, 1, file_size, fp);
		pri_key_buf[read_size] = '\0';
		fclose(fp);
		private_key = pri_key_buf;

		// Read app secret
		fp = fopen(app_secret_path.c_str(), "r");
		if (!fp) {
			printf("Can not open app secret file %s\n", app_secret_path.c_str());
			return false;
		}

		fseek(fp, 0, SEEK_END);
		file_size = ftell(fp);
		fseek(fp, 0, SEEK_SET);

		char* app_secret_buf = (char*)malloc(file_size + 1);
		read_size = fread(app_secret_buf, 1, file_size, fp);
		app_secret_buf[read_size] = '\0';
		fclose(fp);
		app_secret = app_secret_buf;
		free(app_secret_buf);

		app_id = "ww9c08cefb660a4a8c";  // 可以改为从配置文件读取

		// Initialize SDK
		sdk = NewSdk();
		int ret = Init(sdk, app_id.c_str(), app_secret.c_str());
		if (ret != 0) {
			printf("Init sdk failed, ret: %d\n", ret);
			return false;
		}

		return true;
	}

	json get_chat_data(unsigned long long seq = 0, 
					  unsigned long long limit = 1000,
					  unsigned long long timeout = 60) {
		json result;
		Slice_t* chat_data = NewSlice();

		int ret = GetChatData(sdk, seq, limit, "", "", timeout, chat_data);
		if (ret != 0) {
			printf("GetChatData failed, ret: %d\n", ret);
			FreeSlice(chat_data);
			return result;
		}

		json chat_json = json::parse(GetContentFromSlice(chat_data));
		if (chat_json["errcode"] == 0) {
			result["errcode"] = 0;
			result["messages"] = json::array();
			
			for (const auto& msg : chat_json["chatdata"]) {
				json decrypted_msg = decrypt_single_message(msg);
				if (!decrypted_msg.empty()) {
					result["messages"].push_back(decrypted_msg);
				}
			}
		}

		FreeSlice(chat_data);
		return result;
	}
};

int main(int argc, char *argv[]) {
	WeWorkFinanceDecryptor decryptor;
	
	if (!decryptor.init("key/private.pem", "key/app_secret")) {
		return -1;
	}

	json result = decryptor.get_chat_data();
	printf("Decrypted messages:\n%s\n", result.dump(2).c_str());

	return 0;
}
