# WeCom Audit

企业微信会话存档API的Python封装，提供简单易用的接口来获取企业微信的会话记录。

## 安装

```bash
pip install wecom-audit
```

## 功能特点

- 支持获取会话记录
- 支持下载媒体文件
- 提供简单易用的Python API
- 基于企业微信官方C语言SDK封装

## 依赖项

- Python >= 3.11
- CMake
- OpenSSL开发库

## 使用示例

准备一个配置文件`config.json`，示例内容如下：

```json
{
    "corporation_id": "your_corp_id",
    "app_secret": "your_secret",
    "batch_size": 100,
    "private_key_path": "private.pem"
}
```

基础用法：

```python
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

```

## 版权

© 2025 puyuan.tech, Ltd. All rights reserved.

## 许可证

MIT

## 贡献

欢迎提交问题和Pull Request！ 