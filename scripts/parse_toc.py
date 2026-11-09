import json
import re

with open(r'D:\ProjectTest\vortex-flowmeter-dsp\data\pages_data.json', encoding='utf-8') as f:
    data = json.load(f)

toc_text = '\n'.join([d['text'] for d in data[6:12]])
items = []

# Front matter entries
items.append({
    'title': '封面与扉页',
    'book_page': 1,
    'pdf_page_index': 0,
    'level': 1
})
items.append({
    'title': '前言',
    'book_page': 'iii',
    'pdf_page_index': 4,
    'level': 1
})
items.append({
    'title': '目录',
    'book_page': 'v',
    'pdf_page_index': 6,
    'level': 1
})

for line in toc_text.splitlines():
    line = line.strip()
    if not line or '目   录' in line or '目  录' in line or line == '前言':
        continue
    m = re.search(r'^(.*?)\s*·+\s*(\d+)$', line)
    if m:
        title = re.sub(r'\s+', ' ', m.group(1)).strip()
        book_page = int(m.group(2))
        pdf_index = book_page + 11
        if title.startswith('第 ') and '章' in title:
            level = 1
        elif re.match(r'^\d+\.\d+\.\d+\s', title):
            level = 3
        elif re.match(r'^\d+\.\d+\s', title):
            level = 2
        else:
            level = 2
        items.append({
            'title': title,
            'book_page': book_page,
            'pdf_page_index': pdf_index,
            'level': level
        })

print(f"Total TOC items parsed: {len(items)}")

with open(r'D:\ProjectTest\vortex-flowmeter-dsp\data\toc.json', 'w', encoding='utf-8') as f:
    json.dump(items, f, ensure_ascii=False, indent=2)

print("Saved toc.json successfully!")
