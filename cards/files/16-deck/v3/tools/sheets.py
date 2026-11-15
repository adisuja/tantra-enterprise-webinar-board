"""Contact sheets of QA frames: python3 sheets.py <qa dir> <out dir> [only frames matching these slide numbers]"""
import glob, os, sys
from PIL import Image, ImageDraw, ImageFont

src, out = sys.argv[1], sys.argv[2]
only = set(sys.argv[3:])
os.makedirs(out, exist_ok=True)
for f in glob.glob(out + '/*.png'): os.remove(f)
fs = sorted(glob.glob(src + '/*.png'))
if only: fs = [f for f in fs if os.path.basename(f).split('-')[0] in only]
W, H, C, R = 640, 360, 3, 3
try: font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 22)
except Exception: font = ImageFont.load_default()
for i in range(0, len(fs), C * R):
    sheet = Image.new('RGB', (W * C, H * R), (40, 40, 40)); d = ImageDraw.Draw(sheet)
    for j, f in enumerate(fs[i:i + C * R]):
        im = Image.open(f).convert('RGB').resize((W, H), Image.LANCZOS)
        x, y = (j % C) * W, (j // C) * H
        sheet.paste(im, (x, y))
        d.rectangle([x, y, x + 90, y + 30], fill=(255, 0, 90)); d.text((x + 6, y + 3), os.path.basename(f)[:-4], fill='white', font=font)
    sheet.save(f'{out}/s{i // (C * R):02d}.png')
print(len(fs), 'frames,', len(os.listdir(out)), 'sheets')
