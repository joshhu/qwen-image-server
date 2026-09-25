import pytest

from qwen_image_server.server import MAX_PIXELS, ImageRequest, parse_size


@pytest.mark.parametrize("size,expected", [("1344x768", (1344, 768)), ("1024X1024", (1024, 1024))])
def test_parse_size_ok(size, expected):
    assert parse_size(size) == expected


@pytest.mark.parametrize("size", ["abc", "1024", "1024x", "0x1024", "-16x16", "1000x1000", "1x2x3"])
def test_parse_size_invalid(size):
    with pytest.raises(ValueError):
        parse_size(size)


def test_parse_size_too_large():
    side = 16 * 1000
    assert side * side > MAX_PIXELS
    with pytest.raises(ValueError, match="MAX_PIXELS"):
        parse_size(f"{side}x{side}")


def test_request_defaults():
    r = ImageRequest(prompt="cat")
    assert (r.size, r.n, r.response_format, r.seed) == ("1344x768", 1, "b64_json", None)
