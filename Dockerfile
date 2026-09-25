# AMD 官方預建環境：Ubuntu 24.04 + ROCm 7.2 + Python 3.12 + PyTorch 2.9.1（支援 gfx1151）
FROM rocm/pytorch:rocm7.2_ubuntu24.04_py3.12_pytorch_release_2.9.1

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

ENV PYTHONUNBUFFERED=1 \
    HF_HOME=/models \
    FLASH_ATTENTION_TRITON_AMD_ENABLE=TRUE \
    TORCH_ROCM_AOTRITON_ENABLE_EXPERIMENTAL=1

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src

# 裝進 image 內建的 Python，沿用它的 ROCm torch（不重裝 torch）
RUN uv pip install --system --break-system-packages --no-cache ".[gpu]"

EXPOSE 7860
HEALTHCHECK --interval=30s --timeout=5s --start-period=600s \
    CMD python -c "import urllib.request,json,sys; sys.exit(json.load(urllib.request.urlopen('http://localhost:7860/health'))['status']!='ok')"

CMD ["qwen-image-server"]
