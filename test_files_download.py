import json
import wecom_audit
import os
from typing import Optional


def download_media_data(audit: wecom_audit.WeComAudit,
                        output_dir: str,
                        filename: str,
                        sdkfileid: str) -> Optional[str]:
    """
    Download media data from WeChat Work API.

    Args:
        audit: WeComAudit instance
        output_dir: Directory to save the file
        filename: Name of the file
        sdkfileid: SDK file ID from WeChat Work

    Returns:
        str: Path to saved file if successful, None otherwise
    """
    try:
        print(f"Getting media data for {filename}:")
        media_data = audit.get_media_data(sdkfileid)

        if media_data:
            file_path = os.path.join(output_dir, filename)
            with open(file_path, 'wb') as f:
                f.write(media_data)
            print(f"Successfully downloaded media data to: {file_path}")
            return file_path
        else:
            print(f"Failed to get media data for {filename}: No data returned")
            return None

    except Exception as e:
        print(f"Error while getting media data for {filename}: {str(e)}")
        return None


if __name__ == "__main__":
    audit = wecom_audit.WeComAudit("config.puyuan.json")
    messages = audit.get_new_messages(427)

    files_dir = "tmp/files"
    images_dir = "tmp/images"
    mixed_images_dir = "tmp/mixed_images"
    os.makedirs(files_dir, exist_ok=True)
    os.makedirs(images_dir, exist_ok=True)
    os.makedirs(mixed_images_dir, exist_ok=True)

    # download files
    for msg in messages["messages"]:
        if "content" in msg and "file" in msg["content"]:
            sdkfileid = msg["content"]["file"]["sdkfileid"]
            filename = msg["content"]["file"]["filename"]
            download_media_data(audit, files_dir, filename, sdkfileid)

    # download mixed message images
    for msg in messages["messages"]:
        if msg["content"]["msgtype"] == "mixed":
            for item in msg["content"]["mixed"]["item"]:
                if item["type"] == "image":
                    image_info = json.loads(item["content"])
                    sdkfileid = image_info["sdkfileid"]
                    filename = f"{image_info['md5sum']}.jpg"
                    download_media_data(audit, mixed_images_dir, filename, sdkfileid)

    # download images
    for msg in messages["messages"]:
        if "content" in msg and "image" in msg["content"]:
            sdkfileid = msg["content"]["image"]["sdkfileid"]
            filename = f"{msg['content']['image']['md5sum']}.jpg"
            download_media_data(audit, images_dir, filename, sdkfileid)
