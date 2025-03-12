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

## 使用示例

```python
from wecom_audit import WeComAudit

client = WeComAudit("config.json")

# 获取会话记录
messages = client.get_chat_data(seq=0, limit=100)
for msg in messages:
    print(f"From: {msg.from_user}, Content: {msg.content}")

# 下载媒体文件
client.download_media("media_id", "output_file.jpg")
```

## 依赖项

- Python >= 3.11
- CMake
- OpenSSL开发库

## 许可证

MIT

## 贡献

欢迎提交问题和Pull Request！ 