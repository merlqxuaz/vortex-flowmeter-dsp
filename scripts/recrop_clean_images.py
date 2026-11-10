import pypdfium2 as pdfium
from PIL import Image
import json
import os

PDF_PATH = r"D:\xwechat_files\wxid_nh9kfevhm35q22_793f\msg\file\2026-11\涡街流量计的数字信号处理技术_9787030840349.pdf"
BASE_DIR = r"D:\ProjectTest\vortex-flowmeter-dsp"
FORMULAS_DIR = os.path.join(BASE_DIR, "formulas")
DATA_PATH = os.path.join(BASE_DIR, "data", "formulas.json")

doc = pdfium.PdfDocument(PDF_PATH)
forms = json.load(open(DATA_PATH, "r", encoding="utf-8"))

check_eqs = {
    '1.2.2': 14, '2.2.1': 41, '2.2.3': 42, '3.1.2': 52, '3.1.7': 55,
    '3.1.17': 61, '3.1.18': 61, '3.1.21': 64, '3.1.22': 64, '3.1.23': 64,
    '6.1.5': 139, '6.2.1': 146, '6.2.2': 146, '7.1.5': 167, '7.3.1': 169,
    '7.3.2': 169, '7.6.1': 180, '8.1.1': 183, '8.1.7': 192, '8.1.8': 197,
    '8.2.1': 199, '9.2.2': 223, '10.2.3': 252, '10.2.4': 252, '10.2.5': 255,
    '10.2.6': 259, '11.2.3': 283, '11.3.1': 289, '11.3.11': 292
}

scale = 2.5
recropped = 0

for eq_num, pnum in check_eqs.items():
    page = doc[pnum - 1]
    tp = page.get_textpage()
    w_pt, h_pt = page.get_size()
    
    search = tp.search(f'({eq_num})')
    best_m = None
    best_cb = None
    while True:
        m = search.get_next()
        if not m: break
        cb = tp.get_charbox(m[0])
        start_idx = max(0, m[0] - 8)
        prec = tp.get_text_range(start_idx, m[0] - start_idx)
        if cb[0] > 360 and '式' not in prec and '如' not in prec and '见' not in prec:
            best_m = m
            best_cb = cb

    if not best_cb:
        continue

    # Formula height estimate
    band_h = 32
    if eq_num in ['2.2.3', '3.1.2', '3.1.21', '8.1.8', '10.2.4']:
        band_h = 42

    y_bot = max(30, best_cb[1] - 4)
    y_top = min(h_pt - 30, y_bot + band_h)

    # Render high DPI crop
    pix = page.render(scale=scale)
    img = pix.to_pil()

    crop_x1 = int(50 * scale)
    crop_x2 = int((w_pt - 45) * scale)
    crop_y1 = int((h_pt - y_top) * scale)
    crop_y2 = int((h_pt - y_bot) * scale)

    crop = img.crop((crop_x1, crop_y1, crop_x2, crop_y2))
    
    clean_num = eq_num.replace('.', '_')
    out_path = os.path.join(FORMULAS_DIR, f"eq_{clean_num}.webp")
    crop.save(out_path, "WEBP", quality=90)
    recropped += 1
    print(f"Recropped eq_{clean_num}.webp: {crop.size}")

print(f"Successfully recropped {recropped} images.")
