import os
import json
import time

os.environ['PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK'] = 'True'
from paddleocr import PaddleOCR

print("Initializing PaddleOCR with PP-OCRv6...")
ocr = PaddleOCR(use_doc_orientation_classify=False, use_doc_unwarping=False, use_textline_orientation=False, lang='ch')

sample_indices = [0, 4, 12, 15, 48, 50, 113, 241]
samples_result = []

for idx in sample_indices:
    img_name = f"page_{idx+1:03d}.webp"
    img_path = os.path.join(r"D:\ProjectTest\vortex-flowmeter-dsp\pages", img_name)
    print(f"Running OCR on page {idx+1} ({img_name})...")
    
    t0 = time.time()
    res = list(ocr.predict(img_path))
    dt = time.time() - t0
    
    page_rec = []
    if res and len(res) > 0:
        entry = res[0]
        texts = entry.get('rec_texts', [])
        scores = entry.get('rec_scores', [])
        polys = entry.get('dt_polys', [])
        
        for i in range(len(texts)):
            box = polys[i].tolist() if i < len(polys) and hasattr(polys[i], 'tolist') else (polys[i] if i < len(polys) else [])
            score = float(scores[i]) if i < len(scores) else 1.0
            page_rec.append({
                "text": texts[i],
                "score": round(score, 4),
                "box": box
            })
            
    print(f"Page {idx+1}: {len(page_rec)} lines recognized in {dt:.2f}s")
    samples_result.append({
        "page_index": idx,
        "page_number": idx + 1,
        "image": f"pages/{img_name}",
        "ocr_time_seconds": round(dt, 2),
        "lines_count": len(page_rec),
        "results": page_rec
    })

out_file = r"D:\ProjectTest\vortex-flowmeter-dsp\data\ocr_samples.json"
with open(out_file, "w", encoding="utf-8") as f:
    json.dump(samples_result, f, ensure_ascii=False, indent=2)

print(f"All {len(sample_indices)} sample pages OCR completed and saved to {out_file}!")
