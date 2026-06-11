#!/usr/bin/env python3
"""
eBay OAuth ユーザー同意フロー（refresh_token 取得）ヘルパー。
ローカルサーバー不要のコピペ方式。

事前に config.json に client_id / client_secret / ru_name を記入しておくこと。

実行:
  python3 get_token.py
  → 表示されたURLをブラウザで開く → ログイン＆同意
  → リダイレクト先URL（?code=... を含む）をまるごと貼り付け
  → refresh_token が config.json に自動保存される
"""

import json
import base64
import urllib.parse
from pathlib import Path

import requests

HERE = Path(__file__).resolve().parent
CONFIG_PATH = HERE / "config.json"

AUTH_BASE = "https://auth.ebay.com/oauth2/authorize"
TOKEN_URL = "https://api.ebay.com/identity/v1/oauth2/token"
SCOPES = (
    "https://api.ebay.com/oauth/api_scope/sell.inventory "
    "https://api.ebay.com/oauth/api_scope/sell.account"
)


def main():
    cfg = json.loads(CONFIG_PATH.read_text())

    # 1) 同意URL生成
    params = {
        "client_id": cfg["client_id"],
        "redirect_uri": cfg["ru_name"],   # eBayで作ったRuName
        "response_type": "code",
        "scope": SCOPES,
    }
    url = AUTH_BASE + "?" + urllib.parse.urlencode(params)
    print("\n①このURLをブラウザ（eBayにログイン中）で開いて同意してください:\n")
    print(url)
    print("\n②同意後にリダイレクトされたページのURL全体をコピーして貼り付けてください:")
    redirected = input("> ").strip()

    # code抽出
    code = urllib.parse.parse_qs(urllib.parse.urlparse(redirected).query).get("code", [None])[0]
    if not code:
        print("URLに ?code= が見つかりません。やり直してください。")
        return

    # 2) code → refresh_token 交換
    basic = base64.b64encode(f"{cfg['client_id']}:{cfg['client_secret']}".encode()).decode()
    r = requests.post(
        TOKEN_URL,
        headers={"Authorization": f"Basic {basic}",
                 "Content-Type": "application/x-www-form-urlencoded"},
        data={"grant_type": "authorization_code", "code": code,
              "redirect_uri": cfg["ru_name"]},
        timeout=30,
    )
    r.raise_for_status()
    tok = r.json()
    cfg["refresh_token"] = tok["refresh_token"]
    CONFIG_PATH.write_text(json.dumps(cfg, ensure_ascii=False, indent=2))
    print(f"\n✓ refresh_token を config.json に保存しました（有効期限 {tok.get('refresh_token_expires_in', 0)//86400}日）")


if __name__ == "__main__":
    main()
