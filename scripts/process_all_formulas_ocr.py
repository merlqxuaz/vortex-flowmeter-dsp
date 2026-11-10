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

os.makedirs(FORMULAS_DIR, exist_ok=True)

doc = pdfium.PdfDocument(PDF_PATH)
scale = 2.5
REF_WORDS = ['满足式', '由式', '按式', '见式', '如式', '代入式', '根据式', '基于式', '从式', '中，', '中的']

formulas_list = []
seen = set()

t0 = time.time()
print("Step 1: Extracting clean formula images using right-margin charbox and block matching...")

for p_idx in range(len(doc)):
    page = doc[p_idx]
    tp = page.get_textpage()
    w_pt, h_pt = page.get_size()
    txt = tp.get_text_range()
    lines = txt.splitlines()
    
    page_img = None
    
    for l_idx, line in enumerate(lines):
        line_s = line.strip()
        m = re.search(r'\((\s*\d+\s*[\.\-]\s*\d+(?:\s*[\.\-]\s*\d+)?\s*)\)\s*$', line_s)
        if not m:
            continue
            
        num = re.sub(r'\s+', '', m.group(1))
        ch = re.split(r'[\.\-]', num)[0]
        if not (ch.isdigit() and 1 <= int(ch) <= 11):
            continue
        if any(w in line_s for w in REF_WORDS):
            continue
            
        prefix = line_s[:m.start()].strip()
        chinese_chars = len(re.findall(r'[\u4e00-\u9fa5]', prefix))
        if chinese_chars > 6:
            continue
            
        key = (p_idx, num)
        if key in seen:
            continue
        seen.add(key)
        
        # Locate the char position of (num) at the RIGHT MARGIN (X > 330)
        search_target = '(' + num + ')'
        match_start = -1
        match_end = -1
        total_chars = tp.count_chars()
        
        for i in range(total_chars):
            test_sub = tp.get_text_range(i, len(search_target) + 4).replace(' ', '')
            if search_target in test_sub:
                cb = tp.get_charbox(i)
                # CRITICAL: Standalone formula numbers are always on the right margin (X > 320 pt)!
                if cb[0] < 320:
                    continue
                match_start = i
                for k in range(i, min(total_chars, i + len(search_target) + 8)):
                    if ')' in tp.get_text_range(k, 1):
                        match_end = k
                        break
                if match_end == -1:
                    match_end = min(total_chars - 1, i + len(search_target))
                break
                
        if match_start == -1:
            continue
            
        cb_num_start = tp.get_charbox(match_start)
        cb_num_end = tp.get_charbox(match_end)
        y_num_min = min(cb_num_start[1], cb_num_end[1])
        y_num_max = max(cb_num_start[3], cb_num_end[3])
        y_center = (y_num_min + y_num_max) / 2.0
        
        if page_img is None:
            page_img = page.render(scale=scale).to_pil()
            
        # Vertical search band +-45 pt around y_center
        y_top_pdf = min(h_pt - 25, y_center + 45)
        y_bot_pdf = max(25, y_center - 45)
        
        crop_x0 = int(50 * scale)
        crop_x1 = int(435 * scale)
        crop_y0 = max(0, int((h_pt - y_top_pdf) * scale))
        crop_y1 = min(page_img.height, int((h_pt - y_bot_pdf) * scale))
        
        raw_crop = page_img.crop((crop_x0, crop_y0, crop_x1, crop_y1))
        gray = np.array(raw_crop.convert('L'))
        
        row_min = gray.min(axis=1)
        target_r = int((y_top_pdf - y_center) * scale)
        target_r = max(0, min(gray.shape[0] - 1, target_r))
        
        is_text = row_min < 235
        blocks = []
        in_b = False
        st = 0
        for r in range(len(is_text)):
            if is_text[r] and not in_b:
                in_b = True; st = r
            elif not is_text[r] and in_b:
                in_b = False; blocks.append((st, r))
        if in_b: blocks.append((st, len(is_text)))
        
        if not blocks:
            continue
            
        eq_blocks = [b for b in blocks if (b[0] - 8 <= target_r <= b[1] + 8)]
        if not eq_blocks:
            eq_blocks = [min(blocks, key=lambda b: abs((b[0]+b[1])/2 - target_r))]
            
        main_block = eq_blocks[0]
        final_top = main_block[0]
        final_bot = main_block[1]
        
        # Merge fraction parts / multiline formula expressions (gap <= 14 px)
        for b in reversed([b for b in blocks if b[1] < main_block[0]]):
            if final_top - b[1] <= 14:
                final_top = b[0]
            else:
                break
        for b in [b for b in blocks if b[0] > main_block[1]]:
            if b[0] - final_bot <= 14:
                final_bot = b[1]
            else:
                break
                
        final_top = max(0, final_top - 4)
        final_bot = min(gray.shape[0], final_bot + 4)
        
        if final_bot - final_top < 10:
            continue
            
        col_min = gray[final_top:final_bot, :].min(axis=0)
        cols_text = np.where(col_min < 235)[0]
        if len(cols_text) == 0:
            continue
        c_left = max(0, cols_text[0] - 6)
        c_right = min(gray.shape[1], cols_text[-1] + 6)
        
        cropped_eq = raw_crop.crop((c_left, final_top, c_right, final_bot))
        
        clean_num = num.replace('.', '_').replace('-', '_')
        filename = f"eq_{clean_num}.webp"
        filepath = os.path.join(FORMULAS_DIR, filename)
        
        cropped_eq.save(filepath, 'WEBP', quality=95)
        
        formulas_list.append({
            'num': num,
            'clean_num': clean_num,
            'page_index': p_idx,
            'page_num': p_idx + 1,
            'image': f"formulas/{filename}",
            'width': cropped_eq.width,
            'height': cropped_eq.height,
            'raw_line': line_s,
            'ocr_text': ''
        })

print(f"Step 1 Complete: {len(formulas_list)} clean formula images extracted in {round(time.time() - t0, 2)}s.")

print("Step 2: Running PaddleOCR PP-OCRv6 on all formula images to extract formula expressions...")
os.environ['PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK'] = 'True'
from paddleocr import PaddleOCR
ocr = PaddleOCR(use_doc_orientation_classify=False, use_doc_unwarping=False, use_textline_orientation=False, lang='ch')

t_ocr = time.time()
for idx, eq in enumerate(formulas_list):
    img_path = os.path.join(BASE_DIR, eq['image'])
    if not os.path.exists(img_path):
        continue
    try:
        res = list(ocr.predict(img_path))
        if res and len(res) > 0:
            texts = res[0].get('rec_texts', [])
            # Join detected formula parts
            eq_text = ' '.join(texts).strip()
            # Clean up formula numbering if duplicated at end
            eq['ocr_text'] = eq_text
    except Exception as e:
        print(f"Error on {eq['image']}: {e}")
        eq['ocr_text'] = ''
        
    if (idx + 1) % 25 == 0 or idx + 1 == len(formulas_list):
        print(f"  Processed {idx + 1}/{len(formulas_list)} formulas... ({round(time.time() - t_ocr, 1)}s)")

with open(FORMULAS_JSON, 'w', encoding='utf-8') as f:
    json.dump(formulas_list, f, ensure_ascii=False, indent=2)

print(f"Done! All {len(formulas_list)} formulas OCR processed and saved to {FORMULAS_JSON} in {round(time.time() - t0, 2)}s total.")
