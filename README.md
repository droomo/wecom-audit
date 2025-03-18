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
import wecom_audit
import os
import json
if __name__ == "__main__":
    # Initialize WeComAudit with config file
    audit = wecom_audit.WeComAudit("config.json")

    # Get latest messages
    messages = audit.get_new_messages(100)  # Get last 100 messages

    # Download files
    files_dir = "tmp/files"
    os.makedirs(files_dir, exist_ok=True)

    for msg in messages["messages"]:
        # Handle regular files
        if "content" in msg and "file" in msg["content"]:
            sdkfileid = msg["content"]["file"]["sdkfileid"]
            filename = msg["content"]["file"]["filename"]

            media_data = audit.get_media_data(sdkfileid)
            if media_data:
                with open(os.path.join(files_dir, filename), 'wb') as f:
                    f.write(media_data)

        # Handle images
        elif "content" in msg and "image" in msg["content"]:
            sdkfileid = msg["content"]["image"]["sdkfileid"]
            filename = f"{msg['content']['image']['md5sum']}.jpg"

            media_data = audit.get_media_data(sdkfileid)
            if media_data:
                with open(os.path.join(files_dir, filename), 'wb') as f:
                    f.write(media_data)

        # Handle mixed messages with images
        elif msg["content"]["msgtype"] == "mixed":
            for item in msg["content"]["mixed"]["item"]:
                if item["type"] == "image":
                    image_info = json.loads(item["content"])
                    media_data = audit.get_media_data(image_info["sdkfileid"])
                    if media_data:
                        filename = f"{image_info['md5sum']}.jpg"
                        with open(os.path.join(files_dir, filename), 'wb') as f:
                            f.write(media_data)
```

## 版权

© 2025 puyuan.tech, Ltd. All rights reserved.

## 许可证

MIT

## 贡献

欢迎提交问题和Pull Request！ 