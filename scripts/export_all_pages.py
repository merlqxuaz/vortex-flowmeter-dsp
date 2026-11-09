import pypdfium2 as pdfium
import pypdf
import json
import os
import time

PDF_PATH = r"D:\xwechat_files\wxid_nh9kfevhm35q22_793f\msg\file\2026-11\涡街流量计的数字信号处理技术_9787030840349.pdf"
OUT_DIR = r"D:\ProjectTest\vortex-flowmeter-dsp"
PAGES_DIR = os.path.join(OUT_DIR, "pages")
DATA_DIR = os.path.join(OUT_DIR, "data")

os.makedirs(PAGES_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

print("Opening PDF...")
doc = pdfium.PdfDocument(PDF_PATH)
reader = pypdf.PdfReader(PDF_PATH)
num_pages = len(doc)
print(f"Total pages: {num_pages}")

# Render all pages to WebP
t0 = time.time()
pages_data = []

for i in range(num_pages):
    # Render WebP
    page = doc[i]
    pil_img = page.render(scale=1.5).to_pil()
    webp_name = f"page_{i+1:03d}.webp"
    webp_path = os.path.join(PAGES_DIR, webp_name)
    pil_img.save(webp_path, "WEBP", quality=78)

    # Extract text
    txt_page = reader.pages[i].extract_text() or ""
    txt_clean = txt_page.strip()

    pages_data.append({
        "page_index": i,
        "page_number": i + 1,
        "image": f"pages/{webp_name}",
        "text": txt_clean,
        "char_count": len(txt_clean)
    })

    if (i + 1) % 50 == 0 or (i + 1) == num_pages:
        print(f"Processed {i+1}/{num_pages} pages ({time.time()-t0:.1f}s)...")

with open(os.path.join(DATA_DIR, "pages_data.json"), "w", encoding="utf-8") as f:
    json.dump(pages_data, f, ensure_ascii=False, indent=2)

print(f"Done rendering and text extraction in {time.time()-t0:.1f}s!")
