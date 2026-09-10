DOMAIN = "tencent_asr"

CONF_APP_ID = "app_id"
CONF_SECRET_ID = "secret_id"
CONF_SECRET_KEY = "secret_key"
CONF_ENGINE = "engine"
CONF_REGION = "region"

# Engine Model Types
ENGINE_16K_ZH = "16k_zh"
ENGINE_16K_ZH_LARGE = "16k_zh_large"
ENGINE_HY = "Hy-ASR-3.0-preview"

DEFAULT_ENGINE = ENGINE_16K_ZH
DEFAULT_REGION = ""

SUPPORTED_ENGINES = {
    ENGINE_16K_ZH: "16k_zh（通用模型，含免费额度）",
    ENGINE_16K_ZH_LARGE: "16k_zh_large（语音大模型 1.0 版）",
    ENGINE_HY: "Hy-ASR-3.0-preview（语音大模型 2.0 混元版）",
}

# Tencent's real-time ASR endpoint.
ASR_HOST = "asr.cloud.tencent.com"
ASR_PATH = "/asr/v2"

# 200 ms @ 16 kHz / 16 bit / mono = 6400 bytes.
CHUNK_BYTES = 6400
CHUNK_SECONDS = 0.2

