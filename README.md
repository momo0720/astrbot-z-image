# astrbot-z-image

一个支持文生图和图生图接口的 AstrBot 插件。

## 特性

- 支持文生图和图生图。
- 支持异步图生图轮询和多 Key 故障切换。

## 安装

1. 克隆或下载本仓库。
2. 将 `z_image` 目录复制到 AstrBot 的插件目录中。
3. 在 AstrBot 插件配置页填写所需配置。
4. 重启 AstrBot 或重载插件。

## 使用

- 主命令：`/z画图`
- 更多命令示例：见 `z_image/README.md`

## 仓库结构

- `z_image/main.py`
- `z_image/_conf_schema.json`
- `z_image/metadata.yaml`
- `z_image/README.md`

## 说明

- 已将本地敏感 API 地址和 Key 替换为占位内容（如适用）。
- 不包含运行环境中的本地配置文件。
