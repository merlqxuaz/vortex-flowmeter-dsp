import pypdfium2 as pdfium
from PIL import Image
import numpy as np
import json
import re
import os
import time

PDF_PATH = r"D:\xwechat_files\wxid_nh9kfevhm35q22_793f\msg\file\2026-11\涡街流量计的数字信号处理技术_9787030840349.pdf"
BASE_DIR = r"D:\ProjectTest\vortex-flowmeter-dsp"
FORMULAS_DIR = os.path.join(BASE_DIR, "formulas")
DATA_DIR = os.path.join(BASE_DIR, "data")
FORMULAS_JSON = os.path.join(DATA_DIR, "formulas.json")

doc = pdfium.PdfDocument(PDF_PATH)
scale = 2.5

with open(FORMULAS_JSON, encoding='utf-8') as f:
    formulas = json.load(f)

PROSE_WORDS = ['满足', '所示', '式中', '因此', '可以', '根据', '如图', '为', '由式', '行工况', '对于', '平均', '由于', '准确', '角度', '经过']

# Determine which formulas need re-crop
targets = []
for f in formulas:
    txt = f.get('ocr_text', '')
    if any(w in txt for w in PROSE_WORDS) or len(txt) > 80:
        targets.append(f)

print(f"Total formulas to fix: {len(targets)}")

# Step 1: Re-crop images using right-margin and bottom-up expansion
for eq in targets:
    p_idx = eq['page_index']
    num = eq['num']
    page = doc[p_idx]
    tp = page.get_textpage()
    w_pt, h_pt = page.get_size()
    
    target_str = '(' + num + ')'
    cb = None
    for i in range(tp.count_chars()):
        if target_str in tp.get_text_range(i, len(target_str) + 4).replace(' ', ''):
            c = tp.get_charbox(i)
            # Must be standalone formula number at right margin
            if c[0] > 370:
                cb = c
                break
                
    if not cb:
        # Fallback search if parenthesis had extra space
        for i in range(tp.count_chars()):
            test_sub = tp.get_text_range(i, len(target_str) + 8).replace(' ', '')
            if num in test_sub and '(' in test_sub:
                c = tp.get_charbox(i)
                if c[0] > 360:
                    cb = c
                    break
                    
    if not cb:
        print(f"Warning: could not locate right margin for ({num}) on page {p_idx+1}")
        continue
        
    img = page.render(scale=scale).to_pil()
    y_bot_pdf = cb[1] - 4
    y_top_pdf = cb[3] + 45
    
    crop = img.crop((int(50*scale), int((h_pt-y_top_pdf)*scale), int(435*scale), int((h_pt-y_bot_pdf)*scale)))
    gray = np.array(crop.convert('L'))
    is_text = gray.min(axis=1) < 235
    
    rows_text = np.where(is_text)[0]
    if len(rows_text) == 0:
        continue
        
    r_bot = rows_text[-1]
    r_top = r_bot
    for r in range(r_bot, -1, -1):
        if is_text[r]:
            r_top = r
        elif r_top - r > 22:
            break
            
    final_top = max(0, r_top - 4)
    final_bot = min(gray.shape[0], r_bot + 4)
    
    cols = np.where(gray[final_top:final_bot, :].min(axis=0) < 235)[0]
    if len(cols) == 0:
        continue
    final_crop = crop.crop((cols[0]-6, final_top, cols[-1]+6, final_bot))
    
    clean_num = num.replace('.', '_').replace('-', '_')
    filename = f"eq_{clean_num}.webp"
    filepath = os.path.join(FORMULAS_DIR, filename)
    final_crop.save(filepath, 'WEBP', quality=95)
    
    eq['width'] = final_crop.width
    eq['height'] = final_crop.height
    print(f"  Fixed crop for ({num}): {final_crop.size}")

# Step 2: Run PaddleOCR only on the fixed targets
print("\nStep 2: Re-running PaddleOCR on fixed formulas...")
os.environ['PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK'] = 'True'
from paddleocr import PaddleOCR
ocr = PaddleOCR(use_doc_orientation_classify=False, use_doc_unwarping=False, use_textline_orientation=False, lang='ch')

for idx, eq in enumerate(targets):
    img_path = os.path.join(BASE_DIR, eq['image'])
    if not os.path.exists(img_path):
        continue
    try:
        res = list(ocr.predict(img_path))
        if res and len(res) > 0:
            texts = res[0].get('rec_texts', [])
            eq_text = ' '.join(texts).strip()
            # If the OCR picked up prose, clean it
            eq['ocr_text'] = eq_text
            print(f"  ({eq['num']}) OCR -> {repr(eq_text)}")
    except Exception as e:
        print(f"Error on {eq['image']}: {e}")

# Save updated formulas.json
with open(FORMULAS_JSON, 'w', encoding='utf-8') as f:
    json.dump(formulas, f, ensure_ascii=False, indent=2)

print("\nAll formulas updated and saved to data/formulas.json!")
