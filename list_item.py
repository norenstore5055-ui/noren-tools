#!/usr/bin/env python3
"""
noren-store 出品パイプライン CLI。

使い方:
  python3 list_item.py items/eva_death.json            # HTML生成のみ（鍵不要・常に動く）
  python3 list_item.py items/eva_death.json --draft    # ＋eBay下書き作成（要 config.json）
  python3 list_item.py items/eva_death.json --draft --photos 9467-9475   # ＋写真自動UP
  python3 list_item.py items/eva_death.json --publish   # 下書き作成して即公開（写真必須）

商品JSON 1つを正として、HTML生成・eBay下書き・在庫追記・写真アーカイブを一括実行。
"""

import sys
import json
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import html_gen
import inventory as inv

LISTINGS = Path(__file__).resolve().parent.parent / "listings"


def expand_photos(spec: str):
    """'9467-9475' や '9467,9468' を番号リストに展開。"""
    nums = []
    for part in spec.split(","):
        if "-" in part:
            a, b = part.split("-")
            nums += [str(n) for n in range(int(a), int(b) + 1)]
        else:
            nums.append(part.strip())
    return nums


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("item_json")
    ap.add_argument("--draft", action="store_true", help="eBay下書き(未公開オファー)を作成")
    ap.add_argument("--publish", action="store_true", help="下書き作成後すぐ公開")
    ap.add_argument("--photos", help="自動UPする写真番号 例 9467-9475")
    ap.add_argument("--cost", type=int, help="仕入れ値（円）")
    args = ap.parse_args()

    item = json.loads(Path(args.item_json).read_text())

    # 1) HTML生成（常に実行）
    html = html_gen.build_html(item)
    item["_html"] = html
    slug = Path(args.item_json).stem
    out_html = LISTINGS / f"{slug}.html"
    out_html.write_text(html)
    print(f"✓ HTML生成: {out_html}  ({len(html)} chars)")

    if not (args.draft or args.publish):
        print("（--draft/--publish 未指定。HTML生成のみで終了）")
        return

    # 2) eBay下書き作成（要 config.json）
    import ebay_api
    client = ebay_api.EbayClient()
    sku = item["sku"]

    image_urls = None
    if args.photos:
        from archive import WM_OUT
        nums = expand_photos(args.photos)
        image_urls = []
        for n in nums:
            p = WM_OUT / f"IMG_{n}.jpeg"
            url = client.upload_photo(p)
            image_urls.append(url)
            print(f"  ✓ 写真UP: IMG_{n}.jpeg → {url[:60]}...")

    client.put_inventory_item(sku, item, image_urls)
    print(f"✓ inventory_item 作成: SKU={sku}")
    offer_id = client.create_offer(sku, item)
    print(f"✓ 下書き(未公開オファー)作成: offerId={offer_id}")

    listing_id = None
    if args.publish:
        listing_id = client.publish_offer(offer_id)
        print(f"✓ 公開完了: listingId={listing_id}")
        # 3) 在庫追記
        e = item["ebay"]
        item_no = inv.append_item(
            name=item.get("inv_name", item["title"]),
            category=item.get("inv_category", "CD"),
            condition=_cond_label(e.get("condition_id", "4000")),
            price_usd=e["price"],
            ebay_id=listing_id,
            cost_yen=args.cost,
            note=item.get("inv_note", ""),
        )
        print(f"✓ inventory.xlsx 追記: {item_no}")
    else:
        print("→ 写真をeBayでUP後、Seller Hubで公開してください（または再実行で --publish）")


def _cond_label(cid):
    return {"1000": "Brand New", "2750": "Like New", "4000": "Very Good",
            "5000": "Good", "6000": "Acceptable"}.get(str(cid), "Very Good")


if __name__ == "__main__":
    main()
