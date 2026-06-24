# OCR Pipeline — Document Image to Structured Data

> **Tools:** PaddleOCR, Tesseract, Surya, docTR, GOT-OCR2, Vision LLM fallback
> Laminated cascade from fastest/cheapest to most capable.

## The OCR Cascade

```
LEVEL 0: Direct text extraction (PDF text layer, HTML)
   │  Already rendered, no OCR needed — Unstructured handles this
   ▼
LEVEL 1: PaddleOCR (fast, multi-language, GPU-accelerated)
   │  Fails with: handwriting, complex tables, poor scans, stamps
   ▼
LEVEL 2: docTR (better layout, table detection, slower)
   │  Fails with: severe skew, dark backgrounds, very low DPI
   ▼
LEVEL 3: Surya (SOTA 2026 — layout + OCR + reading order + table + 90+ languages)
   │  Fails with: handwriting, signatures, embedded charts with text
   ▼
LEVEL 4: GOT-OCR2 (transformer OCR, end-to-end, handles handwriting)
   │  Fails with: complex multi-modal (text embedded in images/charts)
   ▼
LEVEL 5: Vision LLM (Qwen3-VL / Gemma-3-Vision) — local, free
   │  Fails with: extremely complex layouts, stamps over text
   ▼
LEVEL 6: Claude Vision API (last resort — paid, best accuracy)
```

## PaddleOCR (Level 1 — Primary)

```bash
pip install paddlepaddle-gpu paddleocr  # CUDA for speed
# Or CPU: pip install paddlepaddle paddleocr
```

```python
from paddleocr import PaddleOCR

ocr = PaddleOCR(
    use_angle_cls=True,  # Auto-detect and correct text rotation
    lang="en",           # Or "sv", "de", "fr", "it", "es", "nl", "pl", etc.
    use_gpu=True,
    show_log=False,
)

# Process a screenshot from Browser-Use
result = ocr.ocr("screenshot.png")
# result = [[[[x1,y1],[x2,y2],...], ("Extracted Text", 0.97)], ...]
for line in result[0]:
    text, confidence = line[1]
    if confidence > 0.8:
        print(f"  {text} ({confidence:.0%})")
```

### Multi-Language

```python
ocr = PaddleOCR(
    use_angle_cls=True,
    lang="german",  # de, fr, it, es, pt, nl, pl, cs, hu, sv, da, no, fi
    use_gpu=True,
)
```

### Speed

- GPU (RTX 4090): ~50-100 pages/min
- CPU: ~5-10 pages/min
- Memory: ~2GB VRAM

## Surya (Level 3 — SOTA 2026)

```bash
pip install surya-ocr
```

```python
from surya.ocr import run_ocr
from surya.model.detection.model import load_model as load_det_model, load_processor as load_det_processor
from surya.model.recognition.model import load_model as load_rec_model
from surya.model.recognition.processor import load_processor as load_rec_processor

det_model, det_processor = load_det_model(), load_det_processor()
rec_model, rec_processor = load_rec_model(), load_rec_processor()

predictions = run_ocr(
    ["scan_1.pdf", "scan_2.pdf"],
    ["sv", "de"],  # per-document language list
    det_model, det_processor,
    rec_model, rec_processor,
)

for pred in predictions:
    for line in pred.text_lines:
        print(f"{line.text} (confidence: {line.confidence})")
        print(f"  Position: {line.bbox}")
```

Surya advantages over PaddleOCR:
- Reading-order detection (critical for multi-column forms)
- Table structure extraction
- 90+ languages, including Nordic
- Better handling of low-quality scans

## docTR (Level 2 — Alternative)

```bash
pip install python-doctr[tf]  # TensorFlow
# or: pip install python-doctr[torch]  # PyTorch
```

```python
from doctr.io import DocumentFile
from doctr.models import ocr_predictor

model = ocr_predictor(det_arch="db_resnet50", reco_arch="crnn_vgg16_bn", pretrained=True)
doc = DocumentFile.from_images(["scan.png"])
result = model(doc)
result.show()  # Visualize detected text blocks
json_output = result.export()  # Structured JSON
```

## GOT-OCR2 (Level 4 — Transformer OCR)

```bash
pip install transformers torch
```

```python
from transformers import AutoProcessor, AutoModelForImageTextToText

model = AutoModelForImageTextToText.from_pretrained("stepfun-ai/GOT-OCR2", torch_dtype=torch.float16).to("cuda")
processor = AutoProcessor.from_pretrained("stepfun-ai/GOT-OCR2")

# End-to-end: image → text (no separate detection/recognition)
inputs = processor(images=image, return_tensors="pt").to("cuda")
generated_ids = model.generate(**inputs)
text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
```

Handles handwriting and complex layouts that PaddleOCR/Surya miss.

## Vision LLM (Level 5 — Local, Free)

```python
from openai import OpenAI
import base64

# Qwen3-VL via Ollama/vLLM
client = OpenAI(base_url="http://localhost:11434/v1", api_key="not-needed")

def extract_from_screenshot(image_path: str, instruction: str) -> dict:
    with open(image_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode()

    response = client.chat.completions.create(
        model="qwen3-vl:8b",  # or gemma3-vision
        messages=[{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}},
                {"type": "text", "text": instruction},
            ]
        }],
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)

# Extract Finnish registry data from screenshot
data = extract_from_screenshot(
    "prh_fi_search_result.png",
    "Extract: company name (in Finnish), business ID (Y-tunnus), company form, registered address. Return as JSON."
)
```

## Full Pipeline: Screenshot → Structured Data

```python
async def ocr_extract_from_registry(image_path: str, country: str, registry_type: str) -> dict:
    """Full cascade: try cheapest OCR first, escalate on failure."""

    # Level 1: PaddleOCR
    try:
        result = ocr.ocr(image_path)
        text = " ".join([line[1][0] for line in result[0] if line[1][1] > 0.8])
        if len(text) > 50:  # Meaningful text extracted
            return await llm_extract_from_text(text, country, registry_type)  # LLM structures it
    except Exception:
        pass

    # Level 3: Surya
    try:
        from surya.ocr import run_ocr
        predictions = run_ocr([image_path], [LANG_MAP[country]], ...)
        text = " ".join([line.text for line in predictions[0].text_lines])
        if len(text) > 50:
            return await llm_extract_from_text(text, country, registry_type)
    except Exception:
        pass

    # Level 5: Vision LLM
    try:
        return await vision_llm_extract(image_path, registry_type)
    except Exception:
        pass

    # Level 6: Claude Vision (paid fallback)
    return await claude_vision_extract(image_path, registry_type)
```

## Language Map per Country

| Country | OCR Language Code | PaddleOCR | Surya | Vision LLM |
|---|---|---|---|---|
| Sweden | swe | sv | sv | Qwen3-VL (multilingual) |
| Norway | nor (bokmål) | no | no | Qwen3-VL |
| Denmark | dan | da | da | Qwen3-VL |
| Finland | fin + swe | fi, sv | fi, sv | Qwen3-VL |
| Germany | deu | german | de | Qwen3-VL |
| France | fra | french | fr | Qwen3-VL |
| Italy | ita | italian | it | Qwen3-VL |
| Spain | spa | spanish | es | Qwen3-VL |
| Netherlands | nld | nl | nl | Qwen3-VL |
| Poland | pol | pl | pl | Qwen3-VL |
| Czech | ces | cs | cs | Qwen3-VL |
| Hungary | hun | hu | hu | Qwen3-VL |

## Speed Comparison

| Engine | Pages/min (GPU) | Accuracy (printed) | Accuracy (handwritten) |
|---|---|---|---|
| PaddleOCR | 50-100 | 97% | 60% |
| Surya | 30-50 | 98% | 45% |
| docTR | 20-40 | 96% | 55% |
| GOT-OCR2 | 5-10 | 97% | **85%** |
| Qwen3-VL (8B) | 3-5 | 95% | 80% |
| Claude Vision | 2-3 | **99%** | **92%** |

## Related

- [Unstructured](unstructured.md) — PDF text extraction (no OCR needed if text layer exists)
- [LM Studio + Ollama](lmstudio-ollama.md) — powers Vision LLM level
- [Browser-Use](browser-use.md) — captures the screenshots
- [spaCy NER](spacy.md) — structures the OCR output
