from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import logging
import time
from collections.abc import AsyncIterable

from aiohttp import WSMsgType

from homeassistant.components.stt import (
    AudioBitRates,
    AudioChannels,
    AudioCodecs,
    AudioFormats,
    AudioSampleRates,
    SpeechMetadata,
    SpeechResult,
    SpeechResultState,
    SpeechToTextEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from uuid import uuid4

from .const import (
    ASR_HOST,
    ASR_PATH,
    CHUNK_BYTES,
    CONF_APP_ID,
    CONF_ENGINE,
    CONF_REGION,
    CONF_SECRET_ID,
    CONF_SECRET_KEY,
    DEFAULT_ENGINE,
    ENGINE_HY,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

# Tencent ASR uses voice_format=1 for PCM.
VOICE_FORMAT_PCM = 1


def _sign_url(
    app_id: str,
    secret_id: str,
    secret_key: str,
    engine: str,
    voice_id: str,
) -> str:
    timestamp = int(time.time())
    expired = timestamp + 300
    nonce = int.from_bytes(__import__("secrets").token_bytes(5), "big")

    params = {
        "engine_model_type": engine,
        "expired": expired,
        "nonce": nonce,
        "secretid": secret_id,
        "timestamp": timestamp,
        "voice_format": VOICE_FORMAT_PCM,
        "voice_id": voice_id,
        "filter_punc": 1,
    }

    query = "&".join(
        f"{key}={params[key]}" for key in sorted(params)
    )

    sign_text = f"{ASR_HOST}{ASR_PATH}/{app_id}?{query}"
    signature = base64.b64encode(
        hmac.new(
            secret_key.encode(),
            sign_text.encode(),
            hashlib.sha1,
        ).digest()
    ).decode()

    from urllib.parse import urlencode

    return (
        f"wss://{ASR_HOST}{ASR_PATH}/{app_id}?"
        f"{query}&signature={urlencode({'signature': signature})[10:]}"
    )


async def _read_results(ws, results: dict[int, str], done: asyncio.Event):
    """Receive Tencent ASR results while audio is being uploaded."""
    async for message in ws:
        if message.type != WSMsgType.TEXT:
            if message.type == WSMsgType.ERROR:
                raise RuntimeError(f"Tencent ASR websocket error: {ws.exception()}")
            continue

        try:
            payload = message.json()
        except Exception:
            _LOGGER.warning("Invalid Tencent ASR JSON: %s", message.data)
            continue

        code = payload.get("code", 0)
        if code != 0:
            raise RuntimeError(
                f"Tencent ASR error {code}: {payload.get('message', 'unknown')}"
            )

        result = payload.get("result") or {}
        text = result.get("voice_text_str") or ""
        index = result.get("index")
        slice_type = result.get("slice_type")

        if text and index is not None:
            # Keep the newest text for each sentence. slice_type=2 is stable.
            results[int(index)] = text
            if slice_type == 2:
                _LOGGER.debug("Tencent ASR final sentence %s: %s", index, text)

        if payload.get("final") == 1:
            done.set()
            return


async def _send_audio(ws, stream: AsyncIterable[bytes]):
    """Send PCM at approximately 1:1 real time, using 200 ms packets."""
    buffer = bytearray()

    async for chunk in stream:
        buffer.extend(chunk)

        while len(buffer) >= CHUNK_BYTES:
            packet = bytes(buffer[:CHUNK_BYTES])
            del buffer[:CHUNK_BYTES]
            await ws.send_bytes(packet)
            await asyncio.sleep(0.2)

    if buffer:
        packet = bytes(buffer) + b"\x00" * (CHUNK_BYTES - len(buffer))
        await ws.send_bytes(packet)
        await asyncio.sleep(0.2)

    # Tencent requires a text message to signal end of audio.
    await ws.send_json({"type": "end"})


class TencentAsrEntity(SpeechToTextEntity):
    _attr_name = "Tencent Cloud ASR"
    _attr_should_poll = False

    def __init__(self, entry: ConfigEntry) -> None:
        self.entry = entry
        self.app_id = entry.data[CONF_APP_ID]
        self.secret_id = entry.data[CONF_SECRET_ID]
        self.secret_key = entry.data[CONF_SECRET_KEY]
        self.engine = entry.options.get(
            CONF_ENGINE, entry.data.get(CONF_ENGINE, DEFAULT_ENGINE)
        )

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.entry.entry_id}"

    @property
    def supported_languages(self) -> list[str]:
        if self.engine == ENGINE_HY:
            return ["zh-CN", "en-US"]
        return ["zh-CN"]

    @property
    def supported_formats(self) -> list[AudioFormats]:
        # HA passes the encoded audio stream according to these metadata.
        return [AudioFormats.WAV]

    @property
    def supported_codecs(self) -> list[AudioCodecs]:
        return [AudioCodecs.PCM]

    @property
    def supported_bit_rates(self) -> list[AudioBitRates]:
        return [AudioBitRates.BITRATE_16]

    @property
    def supported_sample_rates(self) -> list[AudioSampleRates]:
        return [AudioSampleRates.SAMPLERATE_16000]

    @property
    def supported_channels(self) -> list[AudioChannels]:
        return [AudioChannels.CHANNEL_MONO]

    async def async_process_audio_stream(
        self,
        metadata: SpeechMetadata,
        stream: AsyncIterable[bytes],
    ) -> SpeechResult:
        if (
            metadata.sample_rate.value != 16000
            or metadata.channel.value != 1
            or metadata.codec != AudioCodecs.PCM
        ):
            _LOGGER.error(
                "Tencent ASR requires 16 kHz / 16-bit / mono PCM; got %s",
                metadata,
            )
            return SpeechResult(None, SpeechResultState.ERROR)

        voice_id = str(uuid4())
        url = _sign_url(
            self.app_id,
            self.secret_id,
            self.secret_key,
            self.engine,
            voice_id,
        )

        session = async_get_clientsession(self.hass)
        results: dict[int, str] = {}
        done = asyncio.Event()

        try:
            async with session.ws_connect(
                url,
                heartbeat=30,
                max_msg_size=2 * 1024 * 1024,
            ) as ws:
                reader = asyncio.create_task(_read_results(ws, results, done))

                try:
                    await _send_audio(ws, stream)

                    # Wait for Tencent's final=1. The server then closes the WS.
                    try:
                        await asyncio.wait_for(done.wait(), timeout=10)
                    except asyncio.TimeoutError:
                        _LOGGER.warning(
                            "Tencent ASR did not return final=1 within timeout"
                        )
                finally:
                    if not reader.done():
                        reader.cancel()
                    await asyncio.gather(reader, return_exceptions=True)

        except Exception as err:
            _LOGGER.exception("Tencent ASR request failed: %s", err)
            return SpeechResult(None, SpeechResultState.ERROR)

        final_text = "".join(
            results[index] for index in sorted(results)
        ).strip()

        if not final_text:
            _LOGGER.warning("Tencent ASR returned no text")
            return SpeechResult(None, SpeechResultState.ERROR)

        _LOGGER.debug("Tencent ASR result: %s", final_text)
        return SpeechResult(final_text, SpeechResultState.SUCCESS)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([TencentAsrEntity(entry)])
