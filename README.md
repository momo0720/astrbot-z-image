# astrbot-z-image

可直接通过 AstrBot 插件仓库链接安装的独立插件仓库。

## 安装方式

### 方式一：通过 GitHub 链接安装

在 AstrBot 插件安装界面中填入本仓库链接即可。

### 方式二：手动安装

1. 克隆或下载本仓库。
2. 将仓库中的所有文件直接放入 AstrBot 的单个插件目录中。
3. 在 AstrBot 插件配置页填写所需配置。
4. 重启 AstrBot 或重载插件。

## 使用

- 主命令：`/z画图`
- 详细说明：见仓库内 `README.md` 下方内容

## 说明

- `metadata.yaml`、`main.py`、`_conf_schema.json` 已放在仓库根目录，兼容 AstrBot 链接安装。
- 已将本地敏感 API 地址和 Key 替换为占位内容（如适用）。
- 不包含运行环境中的本地配置文件。

- 若你是在补充 `repo` 字段之前安装的旧版本，建议重新安装一次，或手动在已安装插件目录的 `metadata.yaml` 中补上 `repo` 地址后再使用更新功能。

---

通过聊天命令调用图像生成接口出图。

当前命令前缀为 `z`，避免与其他插件冲突。

## 安装

1. 将仓库中的所有文件直接放入 AstrBot 的单个插件目录中。
2. 在 AstrBot 插件配置页填写 `api_base_url`、`api_keys` / `api_key`、文生图模型和图生图模型。
3. 重启 AstrBot 或重载插件后即可使用。

## 命令

- `/z画图 <提示词>`：文生图
- `/z画图 <提示词> + 图片`：图生图
- `/z画图 <提示词>` + 引用一张图片：图生图
- `/z画图帮助`：查看帮助

## 行为

- 纯文字：调用 `z-image-turbo`
- 文字 + 图片：调用 `Qwen-Image-Edit-2511`（异步任务接口 `/v1/async/images/edits`）

## 特性

- 支持多个 API Key
- 每次请求随机打乱 key 顺序
- 单个 key 失败自动重试
- 单个 key 失败后自动切换下一个 key
- 图片下载失败自动重试
- 兼容旧版单 Key 配置 `api_key`

## 默认配置

- API: `https://example.com/v1`
- Text model: `z-image-turbo`
- Edit model: `Qwen-Image-Edit-2511`

可在 AstrBot 插件配置页修改。
