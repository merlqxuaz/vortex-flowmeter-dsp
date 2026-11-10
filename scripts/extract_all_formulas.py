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
print("Scanning and extracting all formulas using precise paragraph-band detection...")

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
        
        # Locate the char position of (num) in page
        search_target = '(' + num + ')'
        match_start = -1
        match_end = -1
        total_chars = tp.count_chars()
        
        for i in range(total_chars):
            test_sub = tp.get_text_range(i, len(search_target) + 4).replace(' ', '')
            if search_target in test_sub:
                match_start = i
                # find where search_target ends
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
        
        # Preceding text: find character directly above formula line
        # Formula expression characters might also be above cb_num (e.g. if formula spans 2 lines)
        # Search backwards for Chinese characters or punctuation of preceding sentence
        y_top_pdf = min(h_pt - 25, y_num_max + 45)
        for j in range(match_start - 1, -1, -1):
            char_j = tp.get_text_range(j, 1)
            # Check if this character is Chinese or ending punctuation
            if re.match(r'[\u4e00-\u9fa5：。！？；]', char_j):
                cb_j = tp.get_charbox(j)
                # If this text character is above the formula number
                if cb_j[1] >= y_num_max - 2:
                    y_top_pdf = cb_j[1] - 1.0
                    break
                    
        # Succeeding text: search forward for Chinese characters or punctuation of next sentence (e.g. 式中，或下一段)
        y_bot_pdf = max(25, y_num_min - 35)
        for j in range(match_end + 1, total_chars):
            char_j = tp.get_text_range(j, 1)
            if re.match(r'[\u4e00-\u9fa5]', char_j):
                cb_j = tp.get_charbox(j)
                if cb_j[3] <= y_num_min + 3:
                    y_bot_pdf = cb_j[3] + 1.0
                    break
                    
        if y_top_pdf <= y_bot_pdf:
            y_top_pdf = y_num_max + 30
            y_bot_pdf = y_num_min - 25
            
        if page_img is None:
            page_img = page.render(scale=scale).to_pil()
            
        # Crop band
        crop_x0 = int(50 * scale)
        crop_x1 = int(435 * scale)
        crop_y0 = max(0, int((h_pt - y_top_pdf) * scale))
        crop_y1 = min(page_img.height, int((h_pt - y_bot_pdf) * scale))
        
        if crop_y1 <= crop_y0 + 10:
            continue
            
        raw_crop = page_img.crop((crop_x0, crop_y0, crop_x1, crop_y1))
        gray = np.array(raw_crop.convert('L'))
        
        # Trim white margins
        row_min = gray.min(axis=1)
        col_min = gray.min(axis=0)
        
        rows_text = np.where(row_min < 235)[0]
        cols_text = np.where(col_min < 235)[0]
        
        if len(rows_text) == 0 or len(cols_text) == 0:
            continue
            
        r_top = max(0, rows_text[0] - 4)
        r_bot = min(gray.shape[0], rows_text[-1] + 4)
        c_left = max(0, cols_text[0] - 8)
        c_right = min(gray.shape[1], cols_text[-1] + 8)
        
        cropped_eq = raw_crop.crop((c_left, r_top, c_right, r_bot))
        
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
            'raw_line': line_s
        })

with open(FORMULAS_JSON, 'w', encoding='utf-8') as f:
    json.dump(formulas_list, f, ensure_ascii=False, indent=2)

elapsed = round(time.time() - t0, 2)
print(f"Extraction complete in {elapsed}s! Processed {len(formulas_list)} formulas.")
