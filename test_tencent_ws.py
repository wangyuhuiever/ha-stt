"""Standalone test script for Tencent Cloud Realtime ASR WebSocket connection."""
import asyncio
import base64
import hashlib
import hmac
import secrets
import time
from urllib.parse import urlencode
import aiohttp

# Replace these with your actual credentials for testing
APP_ID = "xx"
SECRET_ID = "xx"
SECRET_KEY = "xx"
ENGINE = "16k_zh_large"

ASR_HOST = "asr.cloud.tencent.com"
ASR_PATH = "/asr/v2"


def sign_url(app_id: str, secret_id: str, secret_key: str, engine: str, voice_id: str) -> str:
    timestamp = int(time.time())
    expired = timestamp + 300
    nonce = int.from_bytes(secrets.token_bytes(5), "big")

    params = {
        "engine_model_type": engine,
        "expired": expired,
        "nonce": nonce,
        "secretid": secret_id,
        "timestamp": timestamp,
        "voice_format": 1,  # 1 for PCM
        "voice_id": voice_id,
        "filter_punc": 1,
    }

    query = "&".join(f"{key}={params[key]}" for key in sorted(params))
    sign_text = f"{ASR_HOST}{ASR_PATH}/{app_id}?{query}"
    signature = base64.b64encode(
        hmac.new(secret_key.encode(), sign_text.encode(), hashlib.sha1).digest()
    ).decode()

    return f"wss://{ASR_HOST}{ASR_PATH}/{app_id}?{query}&signature={urlencode({'signature': signature})[10:]}"


async def main():
    if APP_ID == "YOUR_APP_ID":
        print("[!] 请先在脚本中填入有效的 APP_ID, SECRET_ID 和 SECRET_KEY")
        return

    voice_id = "test-" + str(int(time.time()))
    url = sign_url(APP_ID, SECRET_ID, SECRET_KEY, ENGINE, voice_id)
    print(f"[*] 正在连接腾讯云 ASR WebSocket...")

    async with aiohttp.ClientSession() as session:
        try:
            async with session.ws_connect(url, timeout=10) as ws:
                print("[+] WebSocket 连接成功！鉴权与签名通过。")
                # 发送结束标记
                await ws.send_json({"type": "end"})
                async for msg in ws:
                    print("<- 收到响应:", msg.data)
                    break
        except Exception as e:
            print(f"[-] 连接失败: {e}")


if __name__ == "__main__":
    asyncio.run(main())
