import sys
sys.path.insert(0, r"c:\python\Document_Processor\src")

import fitz

doc = fitz.open("sample.pdf")
for pg_num in range(len(doc)):
    page = doc[pg_num]
    blocks = page.get_text("blocks")
    text = page.get_text("text")
    area = page.rect.width * page.rect.height
    cov = sum((b[2]-b[0])*(b[3]-b[1]) for b in blocks if len(b)>=7 and b[6]==0)
    print(f"\n=== Page {pg_num+1} ===")
    print(f"  chars: {len(text.strip())}")
    print(f"  blocks: {len(blocks)}")
    print(f"  page_area: {area:.0f}px2")
    print(f"  covered_area: {cov:.0f}px2")
    print(f"  text_coverage: {cov/area:.4f}")
    print(f"  block details: {[(round(b[0]),round(b[1]),round(b[2]),round(b[3])) for b in blocks]}")
doc.close()
