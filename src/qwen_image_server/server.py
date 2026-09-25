"""OpenAI-compatible /v1/images/generations endpoint backed by Qwen-Image-2.1."""

import base64
import io
import os
import threading
import time
from collections.abc import Callable
from contextlib import asynccontextmanager
from typing import Any, Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

MODEL_ID = os.getenv("MODEL_ID", "Qwen/Qwen-Image-2.1")
DEFAULT_STEPS = int(os.getenv("STEPS", "40"))
MAX_PIXELS = int(os.getenv("MAX_PIXELS", str(2752 * 1536)))


class ImageRequest(BaseModel):
    prompt: str = Field(min_length=1)
    size: str = "1344x768"
    n: int = Field(default=1, ge=1, le=4)
    steps: int = Field(default=DEFAULT_STEPS, ge=1, le=100)
    seed: int | None = None
    response_format: Literal["b64_json"] = "b64_json"
    model: str | None = None  # OpenAI 相容欄位，忽略


def parse_size(size: str) -> tuple[int, int]:
    """'WxH' → (w, h)；尺寸需為 16 的倍數，總像素不得超過 MAX_PIXELS。"""
    try:
        w, h = (int(v) for v in size.lower().split("x"))
    except ValueError:
        raise ValueError(f"size must look like '1344x768', got {size!r}")
    if w <= 0 or h <= 0:
        raise ValueError("width and height must be positive")
    if w % 16 or h % 16:
        raise ValueError("width and height must be multiples of 16")
    if w * h > MAX_PIXELS:
        raise ValueError(f"{w}x{h} exceeds MAX_PIXELS={MAX_PIXELS}")
    return w, h


def load_qwen_pipeline() -> Callable[..., list[Any]]:
    """載入 diffusers pipeline，回傳 generate(prompt, width, height, steps, seed, n) -> [PIL.Image]."""
    import torch
    from diffusers import QwenImage21Pipeline

    # ROCm 版 PyTorch 的 device 名稱仍是 "cuda"
    pipe = QwenImage21Pipeline.from_pretrained(MODEL_ID, torch_dtype=torch.bfloat16).to("cuda")

    def generate(prompt, width, height, steps, seed, n):
        g = torch.Generator("cuda").manual_seed(seed) if seed is not None else None
        return pipe(
            prompt=prompt, width=width, height=height,
            num_inference_steps=steps, generator=g, num_images_per_prompt=n,
        ).images

    return generate


def create_app(loader: Callable[[], Callable[..., list[Any]]] = load_qwen_pipeline) -> FastAPI:
    state: dict[str, Any] = {}
    lock = threading.Lock()  # 一次只跑一個請求，避免記憶體爆掉

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        state["generate"] = loader()
        yield
        state.clear()

    app = FastAPI(title="qwen-image-server", lifespan=lifespan)

    @app.get("/health")
    def health():
        return {"status": "ok" if "generate" in state else "loading", "model": MODEL_ID}

    @app.post("/v1/images/generations")
    def generations(req: ImageRequest):
        try:
            w, h = parse_size(req.size)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        with lock:
            images = state["generate"](req.prompt, w, h, req.steps, req.seed, req.n)
        data = []
        for img in images:
            buf = io.BytesIO()
            img.save(buf, "PNG")  # RGBA 會保留透明通道
            data.append({"b64_json": base64.b64encode(buf.getvalue()).decode()})
        return {"created": int(time.time()), "data": data}

    return app


def main():
    import uvicorn

    uvicorn.run(create_app(), host=os.getenv("HOST", "0.0.0.0"), port=int(os.getenv("PORT", "7860")))
