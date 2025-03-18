#include "wecom_audit.h"
#include "C_sdk/WeWorkFinanceSdk_C.h"
#include <stdio.h>
#include <stdlib.h>
#include <string>
#include <openssl/rsa.h>
#include <openssl/pem.h>
#include <openssl/err.h>
#include <openssl/bio.h>
#include <nlohmann/json.hpp>
#include <vector>
#include <fstream>

using std::string;
using json = nlohmann::json;

class WeWorkFinanceDecryptor {
private:
	WeWorkFinanceSdk_t* sdk;
	const char* private_key;
	json config;

	void load_config_from_string(const string& config_json) {
		try {
			config = json::parse(config_json);
		} catch (const std::exception& e) {
			throw std::runtime_error("Failed to parse config JSON: " + string(e.what()));
		}

		if (!config.contains("corporation_id") || 
			!config.contains("app_secret") || 
			!config.contains("batch_size") ||
			!config.contains("private_key_path")) {
			throw std::runtime_error("Missing required fields in config");
		}
	}

	void load_config(const string& config_path) {
		std::ifstream config_file(config_path);
		if (!config_file.is_open()) {
			throw std::runtime_error("Cannot open config file: " + config_path);
		}
		config = json::parse(config_file);
		
		// Validate required fields
		if (!config.contains("corporation_id") || 
			!config.contains("app_secret") || 
			!config.contains("batch_size") ||
			!config.contains("private_key_path")) {
			throw std::runtime_error("Missing required fields in config file");
		}
	}

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

		// Perform base64 decode
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

		// Perform RSA decryption
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
		
		// Preserve original fields
		json original_fields = {
			{"seq", msg["seq"]},
			{"msgid", msg["msgid"]}
		};
		
		string decrypted_key = rsa_decrypt(encrypt_random_key);
		if (decrypted_key.empty()) {
			printf("Failed to decrypt random key\n");
			return json();
		}

		Slice_t* decrypted_msg = NewSlice();
		int ret = DecryptData(decrypted_key.c_str(), encrypt_chat_msg.c_str(), decrypted_msg);
		if (ret != 0) {
			printf("Failed to decrypt message, ret: %d\n", ret);
			FreeSlice(decrypted_msg);
			return json();
		}

		json decrypted_json = json::parse(GetContentFromSlice(decrypted_msg));
		json complete_msg = original_fields;
		complete_msg["content"] = decrypted_json;

		FreeSlice(decrypted_msg);
		return complete_msg;
	}

public:
	WeWorkFinanceDecryptor() : sdk(nullptr), private_key(nullptr) {}
	
	~WeWorkFinanceDecryptor() {
		if (sdk) {
			DestroySdk(sdk);
		}
		if (private_key) {
			free((void*)private_key);
		}
	}

	bool init(const string& config_json) {
		try {
			load_config_from_string(config_json);
		} catch (const std::exception& e) {
			printf("Failed to load config: %s\n", e.what());
			return false;
		}

		// Load private key
		FILE* fp = fopen(config["private_key_path"].get<string>().c_str(), "r");
		if (!fp) {
			printf("Can not open private key file %s\n", 
				   config["private_key_path"].get<string>().c_str());
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

		sdk = NewSdk();
		int ret = Init(sdk, 
					  config["corporation_id"].get<string>().c_str(), 
					  config["app_secret"].get<string>().c_str());
		if (ret != 0) {
			printf("Init sdk failed, ret: %d\n", ret);
			return false;
		}

		return true;
	}

	json get_chat_data(unsigned long long seq, 
					  unsigned long long limit,
					  unsigned long long timeout) {
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

	// Retrieve all messages starting from the specified seq
	json get_all_chat_data(unsigned long long start_seq = 0, unsigned long long timeout = 60) {
		json result;
		result["errcode"] = 0;
		result["messages"] = json::array();
		
		unsigned long long current_seq = start_seq;
		const unsigned int LIMIT = config["batch_size"].get<unsigned int>();
		bool has_more = true;
		
		while (has_more) {
			json batch = get_chat_data(current_seq, LIMIT, timeout);

			if (batch.contains("errcode") && batch["errcode"] != 0) {
				result["errcode"] = batch["errcode"];
				result["errmsg"] = batch.value("errmsg", "Unknown error");
				return result;
			}

			if (batch.empty()) {
				result["errcode"] = -1;
				result["errmsg"] = "Failed to get chat data";
				return result;
			}

			if (!batch.contains("messages") || batch["messages"].empty()) {
				has_more = false;
				continue;
			}
			
			for (const auto& msg : batch["messages"]) {
				result["messages"].push_back(msg);
				current_seq = msg["seq"].get<unsigned long long>();
			}
			
			has_more = (batch["messages"].size() == LIMIT);
			
			printf("Retrieved %zu messages, current seq: %llu\n", 
				   result["messages"].size(), current_seq);
		}

		printf("Total messages retrieved: %zu\n", result["messages"].size());
		return result;
	}

	MediaData_Bytes* download_media_data(const string& sdkfileid) {
		MediaData_t* media_data = NewMediaData();
		string index;
		int is_finish = 0;
		std::vector<char> complete_data;

		try {
			while (is_finish == 0) {
				int ret = GetMediaData(this->sdk,
									 index.c_str(),
									 sdkfileid.c_str(),
									 "", // proxy_host
									 "", // proxy_password
									 60, // timeout
									 media_data);

				if (ret != 0) {
					printf("Failed to get media data, ret: %d\n", ret);
					FreeMediaData(media_data);
					return nullptr;
				}

				complete_data.insert(complete_data.end(),
								   media_data->data,
								   media_data->data + media_data->data_len);

				index = media_data->outindexbuf;
				is_finish = media_data->is_finish;
			}

			MediaData_Bytes* result = new MediaData_Bytes;
			result->data = new char[complete_data.size()];
			result->size = complete_data.size();
			memcpy(result->data, complete_data.data(), complete_data.size());

			FreeMediaData(media_data);
			return result;

		} catch (const std::exception& e) {
			printf("Error downloading media data: %s\n", e.what());
			FreeMediaData(media_data);
			return nullptr;
		}
	}
};

extern "C" {
	void* create_decryptor() {
		return new WeWorkFinanceDecryptor();
	}

	bool init_decryptor(void* decryptor, const char* config_json) {
		if (!decryptor) return false;
		return static_cast<WeWorkFinanceDecryptor*>(decryptor)->init(config_json);
	}

	const char* get_new_messages(void* decryptor, unsigned long long seq) {
		if (!decryptor) return nullptr;
		
		WeWorkFinanceDecryptor* dec = static_cast<WeWorkFinanceDecryptor*>(decryptor);
		json result = dec->get_all_chat_data(seq);

		string* str = new string(result.dump());
		return str->c_str();
	}

	void destroy_decryptor(void* decryptor) {
		if (decryptor) {
			delete static_cast<WeWorkFinanceDecryptor*>(decryptor);
		}
	}

	void free_string(char* str) {
		if (str) {
			delete[] str;
		}
	}

	MediaData_Bytes* get_media_data(void* decryptor, const char* sdkfileid) {
		WeWorkFinanceDecryptor* dec = static_cast<WeWorkFinanceDecryptor*>(decryptor);
		return dec->download_media_data(sdkfileid);
	}

	void free_media_data(MediaData_Bytes* data) {
		if (data) {
			if (data->data) {
				delete[] data->data;
			}
			delete data;
		}
	}
}

int main(int argc, char* argv[]) {
	if (argc != 2) {
		printf("Usage: %s <config_path>\n", argv[0]);
		return 1;
	}

	std::ifstream config_file(argv[1]);
	if (!config_file.is_open()) {
		printf("Cannot open config file: %s\n", argv[1]);
		return 1;
	}
	
	string config_json = string(
		std::istreambuf_iterator<char>(config_file),
		std::istreambuf_iterator<char>()
	);

	WeWorkFinanceDecryptor decryptor;
	if (!decryptor.init(config_json)) {
		printf("Failed to initialize decryptor\n");
		return 1;
	}

	json messages = decryptor.get_all_chat_data();
	if (messages.contains("errcode") && messages["errcode"] != 0) {
		printf("Failed to get messages: %s\n", messages.value("errmsg", "Unknown error").c_str());
		return 1;
	}

	json sender_messages;
	for (const auto& msg : messages["messages"]) {
		std::string sender = msg["content"]["from"];
		if (!sender_messages.contains(sender)) {
			sender_messages[sender] = json::array();
		}
		sender_messages[sender].push_back(msg);
	}

	std::ofstream out_file("messages.json");
	out_file << messages.dump(2);
	out_file.close();

	system("mkdir -p data/by_sender");

	for (const auto& [sender, msgs] : sender_messages.items()) {
		std::ofstream sender_file("data/by_sender/" + sender + ".json");
		sender_file << msgs.dump(2);
		sender_file.close();
	}

	printf("Successfully processed %zu messages\n", messages["messages"].size());
	return 0;
}
