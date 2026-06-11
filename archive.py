"""
出品済み写真のアーカイブヘルパー。
watermark_output と watermark_input の対象写真を
出品済み/{型番}_{商品名}_{eBay ID}/ に移動（originals/ にオリジナルも退避）。
"""

import re
import shutil
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent / "商品写真素材"
WM_IN = BASE / "watermark_input"
WM_OUT = BASE / "watermark_output"
SOLD = BASE / "出品済み"


def _safe(s: str) -> str:
    """フォルダ名に使えない文字を除去・短縮。"""
    s = re.sub(r'[\\/:*?"<>|]', "", s)
    return s.strip()[:40]


def archive(catalog, name, ebay_id, img_numbers=None):
    """
    catalog: 型番（例 KICA-360）
    name: 商品名（例 EVA_Death）
    ebay_id: eBay出品ID
    img_numbers: ['9467', ...] 指定なら該当のみ、None なら watermark_output 全件
    戻り値: 移動した枚数
    """
    folder = SOLD / f"{_safe(catalog)}_{_safe(name)}_{ebay_id}"
    (folder / "originals").mkdir(parents=True, exist_ok=True)

    if img_numbers:
        out_files = [WM_OUT / f"IMG_{n}.jpeg" for n in img_numbers]
        in_files = [WM_IN / f"IMG_{n}.jpeg" for n in img_numbers]
    else:
        out_files = sorted(WM_OUT.glob("IMG_*.jpeg"))
        in_files = [WM_IN / f.name for f in out_files]

    moved = 0
    for f in out_files:
        if f.exists():
            shutil.move(str(f), str(folder / f.name))
            moved += 1
    for f in in_files:
        if f.exists():
            shutil.move(str(f), str(folder / "originals" / f.name))

    return moved, folder
