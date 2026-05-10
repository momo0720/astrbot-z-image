import asyncio
import base64
import random

import aiohttp

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.message_components import Image, Reply
from astrbot.api.star import Context, Star


class ZImagePlugin(Star):
    """Z Image image plugin. Text only => text-to-image, text+image => image edit."""

    def __init__(self, context: Context, config=None) -> None:
        super().__init__(context)
        self.config = config or {}

    def _cfg(self, key: str, default=None):
        return self.config.get(key, default)

    def _get_api_keys(self) -> list[str]:
        api_keys = self._cfg("api_keys", []) or []
        if isinstance(api_keys, str):
            api_keys = [line.strip() for line in api_keys.splitlines() if line.strip()]
        if not api_keys and self._cfg("api_key"):
            api_keys = [str(self._cfg("api_key")).strip()]
        return [str(key).strip() for key in api_keys if str(key).strip()]

    def _check_cfg(self) -> str | None:
        if not self._cfg("api_base_url"):
            return "❌ 插件未配置 API 地址。"
        if not self._get_api_keys():
            return "❌ 插件未配置 API Key。"
        if not self._cfg("text_model"):
            return "❌ 插件未配置文生图模型名称。"
        if not self._cfg("edit_model"):
            return "❌ 插件未配置图生图模型名称。"
        return None

    async def _read_image_component(self, comp: Image) -> bytes | None:
        try:
            image_path = await comp.convert_to_file_path()
            with open(image_path, "rb") as f:
                return f.read()
        except Exception as e:
            logger.warning(f"读取输入图片失败: {e}")
            return None

    async def _get_images_from_event(
        self, event: AstrMessageEvent, max_count: int = 1
    ) -> list[bytes]:
        images = []
        for comp in event.message_obj.message:
            if isinstance(comp, Image):
                image_bytes = await self._read_image_component(comp)
                if image_bytes:
                    images.append(image_bytes)
                    if len(images) >= max_count:
                        return images
            elif isinstance(comp, Reply) and comp.chain:
                for quoted_comp in comp.chain:
                    if isinstance(quoted_comp, Image):
                        image_bytes = await self._read_image_component(quoted_comp)
                        if image_bytes:
                            images.append(image_bytes)
                            if len(images) >= max_count:
                                return images
        return images

    async def _download_image(
        self, session: aiohttp.ClientSession, url: str
    ) -> tuple[bytes | None, str | None]:
        last_error = None
        retries = int(self._cfg("download_retries", 2))
        for attempt in range(retries + 1):
            try:
                async with session.get(url) as img_resp:
                    if img_resp.status != 200:
                        last_error = f"图片下载失败：HTTP {img_resp.status}"
                    else:
                        return await img_resp.read(), None
            except Exception as e:
                last_error = str(e)
                logger.warning(
                    f"Z Image 图片下载异常，第 {attempt + 1}/{retries + 1} 次: {e}"
                )
            if attempt < retries:
                await asyncio.sleep(1)
        return None, last_error or "图片下载失败"

    async def _request_image_api(
        self, *, prompt: str, model: str, image_bytes: bytes | None = None
    ) -> tuple[bytes | None, str | None, int | None]:
        base_url = self._cfg("api_base_url", "https://example.com/v1").rstrip("/")
        timeout = aiohttp.ClientTimeout(total=int(self._cfg("timeout", 180)))
        retries = int(self._cfg("request_retries", 2))
        api_keys = self._get_api_keys()
        random.shuffle(api_keys)
        last_error = None

        for key_index, api_key in enumerate(api_keys, start=1):
            for attempt in range(retries + 1):
                try:
                    logger.info(
                        f"Z Image 请求开始，model={model}，key {key_index}/{len(api_keys)}，尝试 {attempt + 1}/{retries + 1}"
                    )
                    async with aiohttp.ClientSession(timeout=timeout) as session:
                        headers = {
                            "Authorization": f"Bearer {api_key}",
                            "X-Failover-Enabled": "true",
                        }

                        if image_bytes:
                            submit_url = f"{base_url}/async/images/edits"
                            form = aiohttp.FormData()
                            form.add_field("model", model)
                            form.add_field("prompt", prompt)
                            form.add_field(
                                "num_inference_steps",
                                str(self._cfg("edit_num_inference_steps", 4)),
                            )
                            form.add_field(
                                "guidance_scale",
                                str(self._cfg("edit_guidance_scale", 1)),
                            )
                            form.add_field("task_types", "edit")
                            form.add_field(
                                "image",
                                image_bytes,
                                filename="image.png",
                                content_type="image/png",
                            )
                            async with session.post(
                                submit_url, headers=headers, data=form
                            ) as resp:
                                try:
                                    data = await resp.json()
                                except Exception:
                                    text = await resp.text()
                                    last_error = f"接口返回非 JSON：HTTP {resp.status} {text[:300]}"
                                    logger.warning(f"Z Image 非 JSON 响应: {last_error}")
                                    if attempt < retries:
                                        await asyncio.sleep(1)
                                        continue
                                    break

                            if resp.status != 200:
                                last_error = (
                                    data.get("error", {}).get("message")
                                    or data.get("message")
                                    or f"HTTP {resp.status}"
                                )
                                logger.warning(
                                    f"Z Image 图生图提交失败，model={model}，key {key_index}/{len(api_keys)}，HTTP {resp.status}: {last_error}"
                                )
                                if attempt < retries:
                                    await asyncio.sleep(1)
                                    continue
                                break

                            task_id = data.get("task_id")
                            if not task_id:
                                last_error = (
                                    data.get("message") or "图生图未返回 task_id"
                                )
                                if attempt < retries:
                                    await asyncio.sleep(1)
                                    continue
                                break

                            poll_url = f"https://example.com/v1/task/{task_id}"
                            poll_retries = int(self._cfg("edit_poll_attempts", 60))
                            poll_interval = int(self._cfg("edit_poll_interval", 5))
                            for _ in range(poll_retries):
                                async with session.get(
                                    poll_url, headers=headers
                                ) as poll_resp:
                                    poll_data = await poll_resp.json()
                                if poll_data.get("error"):
                                    last_error = poll_data.get("message") or str(
                                        poll_data.get("error")
                                    )
                                    break
                                status = poll_data.get("status", "unknown")
                                if status == "success":
                                    output = poll_data.get("output", {})
                                    file_url = output.get("file_url")
                                    if not file_url:
                                        last_error = "图生图成功但未返回 file_url"
                                        break
                                    (
                                        image_bytes_result,
                                        error,
                                    ) = await self._download_image(session, file_url)
                                    if image_bytes_result:
                                        return image_bytes_result, None, key_index
                                    last_error = error
                                    break
                                if status in {"failed", "cancelled"}:
                                    last_error = (
                                        poll_data.get("message")
                                        or f"任务状态: {status}"
                                    )
                                    break
                                await asyncio.sleep(poll_interval)
                            else:
                                last_error = "图生图任务轮询超时"
                        else:
                            submit_url = f"{base_url}/images/generations"
                            headers["Content-Type"] = "application/json"
                            payload = {
                                "model": model,
                                "prompt": prompt,
                                "size": self._cfg("size", "1024x1024"),
                            }
                            async with session.post(
                                submit_url, headers=headers, json=payload
                            ) as resp:
                                try:
                                    data = await resp.json()
                                except Exception:
                                    text = await resp.text()
                                    last_error = f"接口返回非 JSON：HTTP {resp.status} {text[:300]}"
                                    logger.warning(f"Z Image 非 JSON 响应: {last_error}")
                                    if attempt < retries:
                                        await asyncio.sleep(1)
                                        continue
                                    break

                            if resp.status != 200:
                                last_error = (
                                    data.get("error", {}).get("message")
                                    or data.get("message")
                                    or f"HTTP {resp.status}"
                                )
                                logger.warning(
                                    f"Z Image 文生图失败，model={model}，key {key_index}/{len(api_keys)}，HTTP {resp.status}: {last_error}"
                                )
                                if attempt < retries:
                                    await asyncio.sleep(1)
                                    continue
                                break

                            items = data.get("data") or []
                            if not items:
                                last_error = "接口未返回图片数据"
                                if attempt < retries:
                                    await asyncio.sleep(1)
                                    continue
                                break

                            item = items[0]
                            if item.get("b64_json"):
                                return (
                                    base64.b64decode(item["b64_json"]),
                                    None,
                                    key_index,
                                )
                            if item.get("url"):
                                image_bytes_result, error = await self._download_image(
                                    session, item["url"]
                                )
                                if image_bytes_result:
                                    return image_bytes_result, None, key_index
                                last_error = error
                                if attempt < retries:
                                    await asyncio.sleep(1)
                                    continue
                                break

                            last_error = "未找到可用图片字段（b64_json/url）"
                            if attempt < retries:
                                await asyncio.sleep(1)
                                continue
                            break
                except Exception as e:
                    last_error = str(e)
                    logger.warning(
                        f"Z Image 请求异常，model={model}，key {key_index}/{len(api_keys)}，尝试 {attempt + 1}/{retries + 1}: {e}"
                    )
                    if attempt < retries:
                        await asyncio.sleep(1)
                        continue
            logger.warning(f"Z Image 切换下一个 key，当前错误: {last_error}")
        return None, last_error or "画图请求失败", None

    @filter.command("z画图帮助")
    async def draw_help(self, event: AstrMessageEvent):
        yield event.plain_result(
            "🎨 Z Image 画图插件\n"
            "命令：/z画图 <提示词> [可附图片]\n"
            "纯文字：调用 z-image-turbo 文生图\n"
            "文字+图片：调用 Qwen-Image-Edit-2511 图生图\n"
            "特性：支持多个 API Key、失败自动重试并切换 Key"
        )

    @filter.command("z画图")
    async def draw_image(self, event: AstrMessageEvent):
        err = self._check_cfg()
        if err:
            yield event.plain_result(err)
            return

        prompt = event.message_str.strip()
        if prompt.startswith("/z画图"):
            prompt = prompt[len("/z画图") :].strip()
        elif prompt.startswith("z画图"):
            prompt = prompt[len("z画图") :].strip()
        if not prompt:
            yield event.plain_result("用法：/z画图 <提示词>")
            return

        try:
            image_inputs = await self._get_images_from_event(event, max_count=1)
            source_image = image_inputs[0] if image_inputs else None
            model = (
                self._cfg("edit_model", "Qwen-Image-Edit-2511")
                if source_image
                else self._cfg("text_model", "z-image-turbo")
            )
            mode = "图生图" if source_image else "文生图"
            yield event.plain_result(f"🎨 正在进行[{mode}]，请稍候…")
            image_bytes, error, key_index = await self._request_image_api(
                prompt=prompt, model=model, image_bytes=source_image
            )
            if error:
                yield event.plain_result(f"❌ 画图失败：{error}")
                return
            key_tag = f"#key{key_index}" if key_index else "#key?"
            yield (
                event.make_result()
                .message(
                    f"🖼️ 模式：{mode}\n模型：{model}\n使用：{key_tag}\n提示词：{prompt}"
                )
                .base64_image(base64.b64encode(image_bytes).decode())
            )
        except Exception as e:
            logger.error(f"Z Image 画图异常: {e}")
            yield event.plain_result(f"❌ 画图失败：{e}")
