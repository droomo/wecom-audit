import json
import wecom_audit
import os

if __name__ == "__main__":
    audit = wecom_audit.WeComAudit("config.json")
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

            try:
                print(f"Getting media data for {filename} with sdkfileid: {sdkfileid}")
                media_data = audit.get_media_data(sdkfileid)

                if media_data:
                    file_path = os.path.join(files_dir, filename)
                    with open(file_path, 'wb') as f:
                        f.write(media_data)
                    print(f"Successfully downloaded media data to: {file_path}")
                else:
                    print(f"Failed to get media data for {filename}: No data returned")
            except Exception as e:
                print(f"Error while getting media data for {filename}: {str(e)}")

    # download mixed message images
    for msg in messages["messages"]:
        if msg["content"]["msgtype"] == "mixed":
            for item in msg["content"]["mixed"]["item"]:
                if item["type"] == "image":
                    image_info = json.loads(item["content"])
                    sdkfileid = image_info["sdkfileid"]
                    md5sum = image_info["md5sum"]

                    try:
                        print(f"Getting mixed message image with md5sum: {md5sum}")
                        media_data = audit.get_media_data(sdkfileid)

                        if media_data:
                            file_path = os.path.join(mixed_images_dir, f"{md5sum}.jpg")
                            with open(file_path, 'wb') as f:
                                f.write(media_data)
                            print(f"Successfully downloaded mixed message image to: {file_path}")
                        else:
                            print(f"Failed to get mixed message image: {md5sum}")
                    except Exception as e:
                        print(f"Error while getting mixed message image {md5sum}: {str(e)}")

    # download images
    for msg in messages["messages"]:
        if "content" in msg and "image" in msg["content"]:
            sdkfileid = msg["content"]["image"]["sdkfileid"]
            filename = msg["content"]["image"]["md5sum"]+ ".jpg"

            try:
                print(f"Getting media data for {filename} with sdkfileid: {sdkfileid}")
                media_data = audit.get_media_data(sdkfileid)

                if media_data:
                    file_path = os.path.join(images_dir, filename)
                    with open(file_path, 'wb') as f:
                        f.write(media_data)
                    print(f"Successfully downloaded media data to: {file_path}")
                else:
                    print(f"Failed to get media data for {filename}: No data returned")
            except Exception as e:
                print(f"Error while getting media data for {filename}: {str(e)}")
