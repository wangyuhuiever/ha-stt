DOMAIN = "tencent_asr"

CONF_APP_ID = "app_id"
CONF_SECRET_ID = "secret_id"
CONF_SECRET_KEY = "secret_key"
CONF_ENGINE = "engine"
CONF_REGION = "region"

DEFAULT_ENGINE = "16k_zh_large"
DEFAULT_REGION = ""

ENGINE_HY = "Hy-ASR-3.0-preview"

# Tencent's real-time ASR endpoint.
ASR_HOST = "asr.cloud.tencent.com"
ASR_PATH = "/asr/v2"

# 200 ms @ 16 kHz / 16 bit / mono = 6400 bytes.
CHUNK_BYTES = 6400
CHUNK_SECONDS = 0.2
