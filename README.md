# 腾讯云 ASR (语音转文本) Home Assistant 自定义集成

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/default)
[![HA Version](https://img.shields.io/badge/Home%20Assistant-2024.1%2B-blue.svg)](https://www.home-assistant.io/)

这是一个专为 **Home Assistant** 开发的**腾讯云实时语音识别 (Tencent Cloud Realtime ASR)** 自定义集成组件，为 Home Assistant 内置的 **Assist 语音助手流水线** 提供低延迟、高精度的中文及多语言语音转文字 (STT) 能力。

---

## ✨ 特性

- **实时流式传输**：基于腾讯云 WebSocket 实时语音识别接口（`/asr/v2`），音频边录边传，毫秒级响应。
- **UI 配置流 (Config Flow)**：无需手动编写复杂的 YAML 配置，在 Home Assistant 前端界面一键配置与修改。
- **支持多引擎切换（通用模型 / 语音大模型）**：
  - `16k_zh`：**通用模型**（默认推荐）。成熟稳定的实时中文通用引擎，识别响应极快，**支持腾讯云通用免费额度/通用资源包**。
  - `16k_zh_large`：**语音大模型 1.0 版**。针对高噪声、远场、口音等复杂场景，识别鲁棒性强（按大模型1.0版计费）。
  - `Hy-ASR-3.0-preview`：**语音大模型 2.0 混元版**。基于腾讯混元大模型，支持中英双语与多方言（按大模型2.0版计费）。
- **原生兼容 Assist**：完美对接 Home Assistant 语音助手流水线（Voice Pipeline / Assist Satellite / 网页语音交互）。
- **纯原生异步**：采用 `aiohttp` 异步 WebSocket 通信，无阻塞轻量化运行。

---

## 🚀 部署与安装方法

### 方法一：手动安装部署（最常用）

1. 进入你的正式 Home Assistant 宿主机或配置目录（即 `configuration.yaml` 所在的目录）。
2. 在该目录下找到或创建 `custom_components` 文件夹。
3. 将本项目中的 `custom_components/tencent_asr` 文件夹完整拷贝到你的 Home Assistant 的 `custom_components/` 目录下：

   ```text
   /config/ (Home Assistant 配置根目录)
   └── custom_components/
       └── tencent_asr/
           ├── __init__.py
           ├── manifest.json
           ├── const.py
           ├── config_flow.py
           ├── stt.py
           ├── strings.json
           └── translations/
   ```

4. **重启 Home Assistant** 以加载插件。

---

### 方法二：通过 Docker 部署挂载

如果你使用的是 Docker 容器化运行的 Home Assistant，只需将 `custom_components/tencent_asr` 挂载到容器的 `/config/custom_components/tencent_asr`：

```bash
docker run -d \
  --name homeassistant \
  --restart unless-stopped \
  -v /path/to/your/ha/config:/config \
  -v /path/to/ha_stt/custom_components/tencent_asr:/config/custom_components/tencent_asr \
  -p 8123:8123 \
  ghcr.io/home-assistant/home-assistant:stable
```

---

### 方法三：通过 HACS 自定义仓库添加

1. 确保已安装并配置好 [HACS](https://hacs.xyz/)。
2. 打开 **HACS -> 集成 (Integrations)**。
3. 点击右上角菜单中的 **自定义代码库 (Custom repositories)**。
4. 输入你的 Git 仓库地址：`ssh://git@git.wangyuhui.top:4022/wangyuhui/ha_stt.git`（或对应 HTTP/HTTPS 地址），类别选择 **Integration (集成)**。
5. 点击添加后，在 HACS 中搜索 **Tencent Cloud ASR** 并点击安装，完成后重启 Home Assistant。

---

## ⚙️ 使用与配置说明

### 1. 添加集成

1. 重启完成后，打开 Home Assistant 前端界面。
2. 进入 **设置 (Settings) -> 设备与服务 (Devices & Services)**。
3. 点击右下角 **添加集成 (Add Integration)**。
4. 搜索 **`Tencent Cloud ASR`**（或 `腾讯云实时语音识别`）。
5. 填写你的腾讯云 API 参数：
   - **AppID**：主账号开发者 AppID（10 位纯数字，在 [账号信息](https://console.cloud.tencent.com/developer) 中查看）。
   - **SecretID**：腾讯云 API 访问密钥 ID（可在 [API 密钥管理](https://console.cloud.tencent.com/cam/capi) 中获取）。
   - **SecretKey**：腾讯云 API 访问密钥 Key。
   - **识别引擎**：默认 `16k_zh`（通用模型，支持免费额度），可选 `16k_zh_large`（语音大模型1.0）或 `Hy-ASR-3.0-preview`（混元大模型2.0）。
6. 点击提交完成添加。

### 2. 配置到语音助手 (Assist)

1. 进入 **设置 (Settings) -> 语音助手 (Voice Assistants)**。
2. 选择你常用的语音流水线（如 `Home Assistant Cloud` 或新建流水线）。
3. 在 **语音转文本 (STT)** 下拉菜单中，选择 **`Tencent Cloud ASR`**。
4. 保存配置。

### 3. 测试语音识别

- 在 **语音助手** 页面，点击流水线右侧的 **运行调试 (Test / Debug)** 按钮。
- 点击麦克风说话，即可看到腾讯云 ASR 实时返回的识别文本与耗时。

---

## 🛠️ 本地开发与调试

本项目基于 Python 3.13 及 `uv` 进行开发和包管理：

```bash
# 1. 克隆并安装依赖
git clone ssh://git@git.wangyuhui.top:4022/wangyuhui/ha_stt.git
cd ha_stt
uv sync

# 2. 单独测试腾讯云 WebSocket 鉴权
uv run python test_tencent_ws.py

# 3. 启动本地 Home Assistant 进行联调
uv run hass -c ./config --debug
```

---

## 📄 License

[MIT License](LICENSE)
