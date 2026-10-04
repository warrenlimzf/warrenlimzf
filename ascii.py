"""Turns src/headshot-cut.png (background removed with rembg) into ASCII rows for the neofetch card."""
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

SRC = Path(__file__).parent / "src" / "headshot-cut.png"
# sparse to dense
RAMP = " .:-=+*#%@"


def portrait(cols=74, aspect=0.5, invert=False):
    """invert=False suits a dark terminal: bright skin becomes dense glyphs.
    invert=True suits a light terminal: dark hair and suit become dense glyphs."""
    im = Image.open(SRC).convert("RGBA")
    im = im.crop((250, 0, 774, 700))  # head and collar, so the face fills the panel
    alpha = np.array(im.split()[3])
    grey = cv2.cvtColor(np.array(im.convert("RGB")), cv2.COLOR_RGB2GRAY)
    grey = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8)).apply(grey)
    rows = int(cols * im.height / im.width * aspect)
    g = cv2.resize(grey, (cols, rows), interpolation=cv2.INTER_AREA) / 255.0
    a = cv2.resize(alpha, (cols, rows), interpolation=cv2.INTER_AREA)
    out = []
    for y in range(rows):
        line = []
        for x in range(cols):
            if a[y, x] < 110:
                line.append(" ")
                continue
            v = 1 - g[y, x] if invert else g[y, x]
            v = 0.08 + 0.92 * v  # keep the silhouette: no foreground cell is blank
            line.append(RAMP[min(len(RAMP) - 1, int(v * len(RAMP)))])
        out.append("".join(line).rstrip())
    return out


if __name__ == "__main__":
    print("\n".join(portrait()))
