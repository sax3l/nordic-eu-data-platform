# Example: OCR Cascade Test
# Tests each OCR engine against a sample image/PDF.
# Run: python examples/test_ocr_cascade.py --input document.png

import argparse
import time
import json
from pathlib import Path

def test_paddleocr(image_path: str) -> dict:
    """Level 1: PaddleOCR (fast, GPU)."""
    from paddleocr import PaddleOCR
    start = time.perf_counter()
    try:
        ocr = PaddleOCR(use_angle_cls=True, lang="en", use_gpu=True, show_log=False)
        result = ocr.ocr(image_path)
        text = " ".join([line[1][0] for line in result[0] if line[1][1] > 0.8])
        latency = (time.perf_counter() - start) * 1000
        return {"engine": "paddleocr", "success": len(text) > 10, "text": text[:500], "latency_ms": latency}
    except Exception as e:
        return {"engine": "paddleocr", "success": False, "error": str(e)[:100]}

def test_tesseract(image_path: str) -> dict:
    """Level 2: Tesseract (reliable fallback)."""
    import pytesseract
    from PIL import Image
    start = time.perf_counter()
    try:
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img, lang="swe+eng")
        latency = (time.perf_counter() - start) * 1000
        return {"engine": "tesseract", "success": len(text) > 10, "text": text[:500], "latency_ms": latency}
    except Exception as e:
        return {"engine": "tesseract", "success": False, "error": str(e)[:100]}

def test_surya(image_path: str) -> dict:
    """Level 3: Surya (SOTA 2026)."""
    start = time.perf_counter()
    try:
        from surya.ocr import run_ocr
        from surya.model.detection.model import load_model as load_det
        from surya.model.detection.processor import load_processor as load_det_proc
        from surya.model.recognition.model import load_model as load_rec
        from surya.model.recognition.processor import load_processor as load_rec_proc

        det_model, det_processor = load_det(), load_det_proc()
        rec_model, rec_processor = load_rec(), load_rec_proc()
        predictions = run_ocr([image_path], ["sv"], det_model, det_processor, rec_model, rec_processor)
        text = " ".join([line.text for pred in predictions for line in pred.text_lines if line.confidence > 0.8])
        latency = (time.perf_counter() - start) * 1000
        return {"engine": "surya", "success": len(text) > 10, "text": text[:500], "latency_ms": latency}
    except Exception as e:
        return {"engine": "surya", "success": False, "error": str(e)[:100]}

def test_vision_llm(image_path: str) -> dict:
    """Level 5: Vision LLM (Qwen3-VL via Ollama)."""
    import base64
    from openai import OpenAI
    start = time.perf_counter()
    try:
        client = OpenAI(base_url="http://localhost:11434/v1", api_key="not-needed")
        with open(image_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode()
        resp = client.chat.completions.create(
            model="qwen3-vl:8b",
            messages=[{"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}},
                {"type": "text", "text": "Extract all visible text from this image. Return the full text."}
            ]}],
            max_tokens=500,
        )
        text = resp.choices[0].message.content
        latency = (time.perf_counter() - start) * 1000
        return {"engine": "vision_llm", "success": bool(text), "text": text[:500], "latency_ms": latency}
    except Exception as e:
        return {"engine": "vision_llm", "success": False, "error": str(e)[:100]}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", "-i", required=True, help="Path to image or PDF")
    args = parser.parse_args()

    if not Path(args.input).exists():
        print(f"File not found: {args.input}")
        return

    results = []

    # Test each engine in cascade order
    for test_fn in [test_paddleocr, test_tesseract, test_surya, test_vision_llm]:
        print(f"\nTesting {test_fn.__name__}...")
        result = test_fn(args.input)
        status = "OK" if result["success"] else "FAIL"
        print(f"  Result: {status} ({result.get('latency_ms', '?')}ms) — {len(result.get('text', ''))} chars")
        if result.get("text"):
            print(f"  Text preview: {result['text'][:200]}...")
        if result.get("error"):
            print(f"  Error: {result['error']}")
        results.append({k: str(v) if isinstance(v, float) else v for k, v in result.items()})

    # Save results
    with open("ocr_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to ocr_test_results.json")

if __name__ == "__main__":
    main()
