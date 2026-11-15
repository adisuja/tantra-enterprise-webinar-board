import sys, os
from PIL import Image, ImageDraw
src, dst, a, b = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
cols, w, h = 3, 640, 360
ids = list(range(a, b + 1))
rows = (len(ids) + cols - 1) // cols
sheet = Image.new('RGB', (cols * w + (cols - 1) * 8, rows * h + (rows - 1) * 8), (40, 40, 48))
d = ImageDraw.Draw(sheet)
for k, i in enumerate(ids):
    p = f'{src}/s{i:02d}.png'
    if not os.path.exists(p): continue
    im = Image.open(p).convert('RGB').resize((w, h), Image.LANCZOS)
    x, y = (k % cols) * (w + 8), (k // cols) * (h + 8)
    sheet.paste(im, (x, y)); d.rectangle([x, y, x + 34, y + 20], fill=(255, 210, 0)); d.text((x + 6, y + 4), str(i), fill=(0, 0, 0))
sheet.save(dst, quality=82)
print(dst, sheet.size)
