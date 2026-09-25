import base64
import io

from PIL import Image


def decode(item):
    return Image.open(io.BytesIO(base64.b64decode(item["b64_json"])))


def test_health(client):
    assert client.get("/health").json()["status"] == "ok"


def test_generate_default(client, fake):
    r = client.post("/v1/images/generations", json={"prompt": "a lighthouse"})
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body["created"], int)
    img = decode(body["data"][0])
    assert img.format == "PNG" and img.size == (1344, 768)
    assert fake.calls[0]["prompt"] == "a lighthouse"


def test_generate_passes_params(client, fake):
    r = client.post("/v1/images/generations",
                    json={"prompt": "x", "size": "1024x1024", "n": 2, "steps": 20, "seed": 7, "model": "ignored"})
    assert r.status_code == 200
    assert len(r.json()["data"]) == 2
    assert fake.calls[0] == dict(prompt="x", width=1024, height=1024, steps=20, seed=7, n=2)


def test_rgba_preserved(client):
    r = client.post("/v1/images/generations",
                    json={"prompt": "icon. This is an RGBA image with transparency", "size": "512x512"})
    assert decode(r.json()["data"][0]).mode == "RGBA"


def test_bad_size_is_400(client, fake):
    r = client.post("/v1/images/generations", json={"prompt": "x", "size": "1000x1000"})
    assert r.status_code == 400 and "16" in r.json()["detail"]
    assert fake.calls == []


def test_validation_errors(client):
    for payload in ({"prompt": ""}, {"prompt": "x", "n": 5}, {"prompt": "x", "response_format": "url"}, {}):
        assert client.post("/v1/images/generations", json=payload).status_code == 422
