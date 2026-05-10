# Z 画图插件

通过聊天命令调用图像生成接口出图。

当前命令前缀为 `z`，避免与其他插件冲突。

## 安装

1. 将 `z_image` 目录复制到 AstrBot 的插件目录中。
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
