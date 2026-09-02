# Tencent Cloud ASR for Home Assistant

Experimental custom integration for Home Assistant 2026.7.x.

It connects Home Assistant STT directly to Tencent Cloud's real-time ASR
WebSocket API. ESPHome Voice Assistant devices do not need to be changed.

Supported initial path:

- 16 kHz
- 16-bit
- mono
- PCM
- zh-CN
- Tencent `16k_zh_large`
- Tencent `Hy-ASR-3.0-preview`

Install by copying `custom_components/tencent_asr` into `/config/custom_components/`,
restart Home Assistant, then add **Tencent Cloud ASR** from Settings > Devices & services.
