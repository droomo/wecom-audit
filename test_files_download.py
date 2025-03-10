import wecom_audit
import os

if __name__ == "__main__":
    audit = wecom_audit.WeComAudit("config.json")
    messages = audit.get_new_messages(7)
    os.system("mkdir -p data/files")
    # Process file data
    for msg in messages["messages"]:
        if "content" in msg and "file" in msg["content"]:
            print(msg["content"]["file"]["filename"])
            save_dir = "data/files"
            if audit.download_files(msg, save_dir):
                print(f"Successfully downloaded: {msg['content']['file']['filename']}")
            else:
                print(f"Failed to download: {msg['content']['file']['filename']}")