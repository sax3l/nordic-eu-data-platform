# OCR Worker — Document Processing Worker
# Polls Redis for OCR jobs, runs PaddleOCR → Tesseract → Surya cascade.
# Part of the nordic-eu-data-platform worker pool.

import asyncio
import json
import os
import time
from pathlib import Path

import redis.asyncio as redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/v1")

redis_client = redis.from_url(REDIS_URL)

async def ocr_paddleocr(image_path: str) -> str:
    """Level 1: PaddleOCR."""
    from paddleocr import PaddleOCR
    ocr = PaddleOCR(use_angle_cls=True, lang="en", use_gpu=True, show_log=False)
    result = ocr.ocr(image_path)
    texts = [line[1][0] for line in result[0] if line[1][1] > 0.8]
    return " ".join(texts)

async def ocr_tesseract(image_path: str) -> str:
    """Level 2: Tesseract."""
    import pytesseract
    from PIL import Image
    img = Image.open(image_path)
    return pytesseract.image_to_string(img, lang="swe+eng")

async def llm_structure_text(text: str) -> dict:
    """Use local LLM to structure OCR output."""
    import httpx
    if len(text) < 20:
        return {"text": text, "structured": {}}
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{OLLAMA_URL}/chat/completions",
            json={
                "model": "phi4:14b",
                "messages": [{"role": "user", "content": (
                    f"Structure this OCR output into JSON. Extract: company_name, org_number_or_tax_id, "
                    f"fiscal_year, revenue, profit, employee_count, and any board_members with names. "
                    f"Text: {text[:3000]}"
                )}],
                "response_format": {"type": "json_object"},
                "temperature": 0.1,
            }
        )
        return json.loads(resp.json()["choices"][0]["message"]["content"])

async def process_ocr_job(task: dict):
    """Process a single OCR job."""
    task_id = task.get("id", "unknown")
    file_path = task.get("file_path")
    job_type = task.get("type", "ocr")

    print(f"[{task_id}] OCR processing {file_path}")

    if not Path(file_path).exists():
        result = {"task_id": task_id, "success": False, "error": "File not found"}
        await redis_client.hset("results", task_id, json.dumps(result))
        return

    start = time.perf_counter()
    text = ""

    # Try PaddleOCR first
    try:
        text = await ocr_paddleocr(file_path)
        if len(text) > 20:
            print(f"[{task_id}] PaddleOCR: {len(text)} chars")
    except Exception as e:
        print(f"[{task_id}] PaddleOCR failed: {e}")

    # Fallback to Tesseract
    if len(text) < 20:
        try:
            text = await ocr_tesseract(file_path)
            print(f"[{task_id}] Tesseract fallback: {len(text)} chars")
        except Exception as e:
            print(f"[{task_id}] Tesseract failed: {e}")

    latency = (time.perf_counter() - start) * 1000
    result = {
        "task_id": task_id,
        "success": len(text) > 10,
        "text": text[:5000],
        "text_length": len(text),
        "latency_ms": latency,
    }

    # Structure if financial document
    if job_type == "financial" and len(text) > 50:
        structured = await llm_structure_text(text)
        result["structured"] = structured

    print(f"[{task_id}] {'SUCCESS' if result['success'] else 'FAILED'} ({latency:.0f}ms, {len(text)} chars)")
    await redis_client.hset("results", task_id, json.dumps(result, default=str))

async def main():
    print("OCR worker starting. Methods: PaddleOCR → Tesseract → LLM structuring")
    while True:
        result = await redis_client.blpop("queue:ocr", timeout=30)
        if result is None:
            continue
        _, task_json = result
        task = json.loads(task_json)
        asyncio.create_task(process_ocr_job(task))

if __name__ == "__main__":
    asyncio.run(main())
