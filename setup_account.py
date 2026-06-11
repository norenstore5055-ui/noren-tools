#!/usr/bin/env python3
"""
config.json の残り（ポリシーID・在庫ロケーション）を eBay Account API から
自動取得して埋める。開発者アカウント承認 → get_token.py 完了後に1回だけ実行。

実行:
  python3 setup_account.py

やること:
  ① payment / return / fulfillment ポリシーを一覧表示し、自動で1件目を選んで config に書く
     （複数ある場合は番号で選択）
  ② 在庫ロケーションが無ければ Nisshin, Aichi で自動登録
"""

import json
from pathlib import Path

import ebay_api

HERE = Path(__file__).resolve().parent
CONFIG_PATH = HERE / "config.json"


def pick(items, label_key, id_key, name):
    """1件なら自動選択、複数なら番号入力。"""
    if not items:
        print(f"  ⚠ {name} が0件。eBayで先に作成してください。")
        return None
    if len(items) == 1:
        it = items[0]
        print(f"  ✓ {name}: {it.get(label_key)} → {it.get(id_key)}")
        return it.get(id_key)
    print(f"  {name} が複数あります:")
    for i, it in enumerate(items):
        print(f"    [{i}] {it.get(label_key)}  (ID {it.get(id_key)})")
    idx = int(input(f"  使う{name}の番号: "))
    return items[idx].get(id_key)


def main():
    cfg = json.loads(CONFIG_PATH.read_text())
    client = ebay_api.EbayClient()

    print("■ ポリシーIDを取得中...")
    pay = client.get_policies("payment_policy").get("paymentPolicies", [])
    ret = client.get_policies("return_policy").get("returnPolicies", [])
    ful = client.get_policies("fulfillment_policy").get("fulfillmentPolicies", [])

    pid = pick(pay, "name", "paymentPolicyId", "支払いポリシー")
    rid = pick(ret, "name", "returnPolicyId", "返品ポリシー")
    fid = pick(ful, "name", "fulfillmentPolicyId", "配送ポリシー")
    if pid: cfg["payment_policy_id"] = pid
    if rid: cfg["return_policy_id"] = rid
    if fid: cfg["fulfillment_policy_id"] = fid

    print("\n■ 在庫ロケーションを確認中...")
    locs = client.get_locations().get("locations", [])
    if locs:
        key = locs[0]["merchantLocationKey"]
        print(f"  ✓ 既存ロケーション: {key}")
        cfg["merchant_location_key"] = key
    else:
        key = cfg.get("merchant_location_key", "noren-store-aichi")
        print(f"  在庫ロケーションが無いので登録します: {key}")
        client.create_location(key, {
            "city": "Nisshin", "stateOrProvince": "Aichi",
            "postalCode": "470-0111", "country": "JP",
        })
        cfg["merchant_location_key"] = key
        print("  ✓ 登録完了")

    CONFIG_PATH.write_text(json.dumps(cfg, ensure_ascii=False, indent=2))
    print("\n✓ config.json を更新しました。これで list_item.py --draft が使えます。")


if __name__ == "__main__":
    main()
