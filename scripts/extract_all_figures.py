import pypdfium2 as pdfium
from PIL import Image
import numpy as np
import json
import re
import os
import time

PDF_PATH = r"D:\xwechat_files\wxid_nh9kfevhm35q22_793f\msg\file\2026-11\涡街流量计的数字信号处理技术_9787030840349.pdf"
BASE_DIR = r"D:\ProjectTest\vortex-flowmeter-dsp"
FIGURES_DIR = os.path.join(BASE_DIR, "figures")
DATA_DIR = os.path.join(BASE_DIR, "data")
PAGES_JSON = os.path.join(DATA_DIR, "pages_data.json")

os.makedirs(FIGURES_DIR, exist_ok=True)

doc = pdfium.PdfDocument(PDF_PATH)
with open(PAGES_JSON, encoding='utf-8') as f:
    pages_data = json.load(f)

EXCLUDE_WORDS = ['所示', '见图', '如图', '表明', '中，', '中的', '中“', '为 ', '是 ', '由图', '按图', '从图', '可以看出', '经过']

figures_list = []
seen_nums = set()

t0 = time.time()
print("Scanning all 306 pages for figures and diagrams...")

for p_idx in range(len(doc)):
    page = doc[p_idx]
    tp = page.get_textpage()
    w_pt, h_pt = page.get_size()
    txt = pages_data[p_idx]['text']
    
    captions = []
    lines = txt.splitlines()
    for i, line in enumerate(lines):
        line_s = line.strip()
        m = re.match(r'^图\s*(\d+\.\d+(?:\.\d+)?)\s*(.*)$', line_s)
        if m:
            num = m.group(1)
            title = m.group(2).strip()
            if not title and i + 1 < len(lines):
                title = lines[i+1].strip()
            if any(w in line_s for w in EXCLUDE_WORDS):
                continue
            if len(line_s) > 50:
                continue
            if num in seen_nums:
                continue
                
            # Search position in page
            s_m = None
            for q in [f"图 {num}", f"图{num}"]:
                s = tp.search(q)
                while True:
                    m_occ = s.get_next()
                    if not m_occ: break
                    st, cnt = m_occ
                    cb = tp.get_charbox(st)
                    snip = tp.get_text_range(st, min(35, tp.count_chars() - st))
                    if any(w in snip for w in ['所示', '见图', '表明', '中的', '为 ']):
                        continue
                    if st > 0 and tp.get_text_range(st-1, 1) in ('如', '按', '由', '见', '从'):
                        continue
                    s_m = cb
                    break
                if s_m: break
                
            if s_m:
                seen_nums.add(num)
                captions.append({
                    'num': num,
                    'title': f"图 {num} {title}".strip(),
                    'cap_box': s_m
                })
                
    if not captions:
        continue
        
    captions.sort(key=lambda c: c['cap_box'][3], reverse=True)
    all_objs = list(page.get_objects())
    
    # Render page high-res
    scale = 2.5
    pil_img = page.render(scale=scale).to_pil()
    w_px, h_px = pil_img.size
    
    for k, cap in enumerate(captions):
        cap_box = cap['cap_box']
        cap_top = cap_box[3]
        start_x = cap_box[0]
        
        # Column scope
        if start_x > 250.0:
            x_min, x_max = 240.0, 435.0
        elif start_x < 80.0:
            x_min, x_max = 45.0, 240.0
        else:
            x_min, x_max = 45.0, 435.0
            
        if k == 0:
            upper_limit = 612.0
        else:
            upper_limit = captions[k-1]['cap_box'][1] - 4.0
            
        # Graphic objects in this column and vertical interval
        objs = [o.get_bounds() for o in all_objs if o.type in (2, 3) and cap_top < (o.get_bounds()[1]+o.get_bounds()[3])/2.0 < upper_limit and (o.get_bounds()[0] < x_max and o.get_bounds()[2] > x_min)]
        
        if objs:
            l = max(40.0, min(b[0] for b in objs) - 5.0)
            b = max(cap_top + 1.0, min(b[1] for b in objs) - 3.0)
            r = min(w_pt - 40.0, max(b[2] for b in objs) + 5.0)
            t = min(upper_limit, max(b[3] for b in objs) + 4.0)
            bbox = (l, b, r, t)
        else:
            bbox = (x_min, cap_top + 3.0, x_max, upper_limit)
            
        # Crop from rendered image
        pad = 4
        x0 = max(0, int((bbox[0] - pad) / w_pt * w_px))
        y0 = max(0, int((h_pt - bbox[3] - pad) / h_pt * h_px))
        x1 = min(w_px, int((bbox[2] + pad) / w_pt * w_px))
        y1 = min(h_px, int((h_pt - bbox[1] + pad) / h_pt * h_px))
        
        if y1 <= y0 or x1 <= x0:
            continue
            
        crop = pil_img.crop((x0, y0, x1, y1))
        
        # Auto-trim white borders around crop
        gray = np.array(crop.convert('L'))
        non_white = np.where(gray < 245)
        if len(non_white[0]) > 20: # has content
            top_pad = max(0, non_white[0].min() - 6)
            bottom_pad = min(gray.shape[0], non_white[0].max() + 7)
            left_pad = max(0, non_white[1].min() - 6)
            right_pad = min(gray.shape[1], non_white[1].max() + 7)
            crop = crop.crop((left_pad, top_pad, right_pad, bottom_pad))
            
        safe_num = cap['num'].replace('.', '_')
        fn = f"fig_{safe_num}.webp"
        save_path = os.path.join(FIGURES_DIR, fn)
        crop.save(save_path, "WEBP", quality=82)
        
        cw, ch = crop.size
        figures_list.append({
            'num': cap['num'],
            'title': cap['title'],
            'page_index': p_idx,
            'page_number': p_idx + 1,
            'image': f"figures/{fn}",
            'width': cw,
            'height': ch,
            'aspect_ratio': round(cw / max(1, ch), 3)
        })

print(f"Extracted {len(figures_list)} figures in {time.time()-t0:.1f}s!")

figures_out = os.path.join(DATA_DIR, "figures.json")
with open(figures_out, "w", encoding="utf-8") as f:
    json.dump(figures_list, f, ensure_ascii=False, indent=2)

print(f"Saved figure metadata to {figures_out}")
