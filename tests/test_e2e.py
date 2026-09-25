"""對真正跑起來的 server 做端到端測試（需 GPU 機器）：E2E_URL=http://<AMD-IP>:7860 uv run pytest -m e2e"""

import base64
import io
import os

import httpx
import pytest
from PIL import Image

URL = os.getenv("E2E_URL")
pytestmark = [pytest.mark.e2e, pytest.mark.skipif(not URL, reason="E2E_URL not set")]


def test_real_generation():
    assert httpx.get(f"{URL}/health", timeout=10).json()["status"] == "ok"
    r = httpx.post(f"{URL}/v1/images/generations",
                   json={"prompt": "a red apple on a white table", "size": "512x512", "steps": 8, "seed": 1},
                   timeout=900)
    r.raise_for_status()
    img = Image.open(io.BytesIO(base64.b64decode(r.json()["data"][0]["b64_json"])))
    assert img.size == (512, 512)
