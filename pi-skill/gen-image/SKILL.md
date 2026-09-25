---
name: gen-image
description: 用本地 Qwen-Image-2.1 生圖服務產生圖片（PPT 插圖、滿版背景、去背圖示、含文字的標題圖）。當簡報或文件需要圖片時使用。
---

# 產生圖片

執行：

    scripts/gen.sh "<prompt>" <輸出路徑.png> [寬x高] [steps]

範例：

    scripts/gen.sh "Isometric illustration of a small data center, soft blue palette, clean flat style" assets/slide03.png 1344x768 25

## 規則

- 模型是 Qwen-Image-2.1，擅長在圖中畫出文字；需要文字時把文字用引號寫在 prompt 裡。
- prompt 要具體：主體、風格、構圖、色調、光線。
- 尺寸必須是 16 的倍數：
  - 滿版背景 16:9：1344x768（草稿）、2752x1536（定稿）
  - 半版配圖：1024x1024
  - 直式配圖：768x1344
- 圖示或去背元素：prompt 結尾加上 `This is an RGBA image with transparency`，會輸出透明背景 PNG。
- 生成很慢（每張可能要數分鐘）。做整份簡報時，先把每頁的 prompt 列給使用者確認，再逐張生成。
- 草稿用 steps 20-25，定稿用 40。
- 生成後用 read 工具看一下圖；不符合就調整 prompt 重生。
- 圖片存在 `./assets/`，再用 python-pptx（`uv run --with python-pptx`）插入投影片。
