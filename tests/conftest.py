import pytest
from fastapi.testclient import TestClient
from PIL import Image

from qwen_image_server.server import create_app


class FakePipeline:
    """取代真正的 diffusers pipeline，記錄呼叫參數並回傳純色圖。"""

    def __init__(self):
        self.calls = []

    def __call__(self, prompt, width, height, steps, seed, n):
        self.calls.append(dict(prompt=prompt, width=width, height=height, steps=steps, seed=seed, n=n))
        mode = "RGBA" if "transparency" in prompt else "RGB"
        return [Image.new(mode, (width, height)) for _ in range(n)]


@pytest.fixture
def fake():
    return FakePipeline()


@pytest.fixture
def client(fake):
    with TestClient(create_app(loader=lambda: fake)) as c:
        yield c
