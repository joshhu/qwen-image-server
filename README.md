# qwen-image-server

把 [Qwen-Image-2.1](https://huggingface.co/Qwen/Qwen-Image-2.1) 包成 **OpenAI 相容的 `/v1/images/generations` API**，跑在 AMD Ryzen AI Max+ 395（Strix Halo, gfx1151, ROCm 7.2）上，並附一個 [pi](https://github.com/earendil-works/pi) skill，讓 pi agent 做 PPT 時能自動生圖。

```
pi agent ──(LLM/VLM)──> DGX Spark: Qwen (vLLM)
    │
    └─ skill: gen-image ──HTTP──> AMD 395+: qwen-image-server ──> Qwen-Image-2.1
```

## 部署（AMD 395+ / Linux）

需求：Docker、ROCm kernel driver（`/dev/kfd`、`/dev/dri` 存在）。

```bash
git clone https://github.com/joshhu/qwen-image-server && cd qwen-image-server
cp .env.example .env        # 視需要調整 STEPS / HF_TOKEN
docker compose up -d --build
docker compose logs -f      # 第一次會下載模型權重，存在 hf-cache volume
curl http://localhost:7860/health   # {"status":"ok",...} 表示模型已載入
```

base image 是 `rocm/pytorch:rocm7.2_ubuntu24.04_py3.12_pytorch_release_2.9.1`，沿用 AMD 預建的 ROCm PyTorch，不另外裝 torch。

## API

`POST /v1/images/generations`

| 欄位 | 預設 | 說明 |
|---|---|---|
| `prompt` | 必填 | 描述；要透明背景就加 `This is an RGBA image with transparency` |
| `size` | `1344x768` | `WxH`，需為 16 的倍數，總像素 ≤ `MAX_PIXELS` |
| `steps` | `STEPS`（40） | 推論步數，草稿可用 20–25 |
| `n` | 1 | 1–4 |
| `seed` | 隨機 | 固定 seed 可重現結果 |
| `response_format` | `b64_json` | 只支援 `b64_json` |

```bash
curl -s http://<AMD-IP>:7860/v1/images/generations \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"A neon sign that reads \"HELLO\"","size":"1024x1024","steps":25}' \
  | jq -r '.data[0].b64_json' | base64 -d > out.png
```

同一時間只處理一個請求（其他請求排隊），避免記憶體爆掉。

環境變數：`MODEL_ID`、`STEPS`、`MAX_PIXELS`、`HOST`、`PORT`、`HF_TOKEN`。

## pi skill

在跑 pi 的機器上：

```bash
cp -r pi-skill/gen-image ~/.pi/agent/skills/
chmod +x ~/.pi/agent/skills/gen-image/scripts/gen.sh
export IMAGE_API_URL=http://<AMD-IP>:7860   # 建議寫進 shell profile
```

需要 `curl`、`jq`、`base64`。使用時 `/model` 選 DGX 上的 Qwen，然後：

```
/skill:gen-image
幫我做一份 10 頁的「XXX」簡報，每頁配一張插圖，輸出 deck.pptx
```

## 開發與測試

```bash
uv sync
uv run pytest --cov=qwen_image_server          # 單元 + 功能測試（用假的 pipeline，不需 GPU）
E2E_URL=http://<AMD-IP>:7860 uv run pytest -m e2e   # 端到端：打真正的 server
```

- `tests/test_unit.py`：尺寸解析與參數驗證
- `tests/test_api.py`：API 行為（用 FakePipeline 取代模型）
- `tests/test_e2e.py`：對實機 server 產生一張 512x512 圖

## 授權

程式碼 MIT。模型權重依 **Qwen Research License**，商業使用前請先確認條款。
