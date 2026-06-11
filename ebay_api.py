"""
eBay Sell API クライアント（noren-store 出品自動化用）。

設計:
- 認証: OAuth2 ユーザートークン（refresh_token から都度 access_token を発行）
- 下書き作成: Inventory API の「未公開オファー」= 現UIの下書きと同等。
  ① createOrReplaceInventoryItem  ② createOffer（unpublished）
  → 写真UP後に publishOffer で公開（人間承認ゲートを維持）
- 写真自動UP: Trading API UploadSiteHostedPictures でローカル画像→eBayホストURL化

認証情報は tools/config.json（gitignore対象）から読む。雛形は config.example.json。
※ APIキー発行・OAuth同意は Koji さん本人の作業（SETUP_ebay_api.md 参照）。
"""

import json
import base64
import time
from pathlib import Path

import requests

HERE = Path(__file__).resolve().parent
CONFIG_PATH = HERE / "config.json"
TOKEN_CACHE = HERE / ".token_cache.json"

# 本番エンドポイント（sandbox に切り替える場合は config の "env" を "sandbox" に）
ENDPOINTS = {
    "production": {
        "oauth": "https://api.ebay.com/identity/v1/oauth2/token",
        "api": "https://api.ebay.com",
        "trading": "https://api.ebay.com/ws/api.dll",
    },
    "sandbox": {
        "oauth": "https://api.sandbox.ebay.com/identity/v1/oauth2/token",
        "api": "https://api.sandbox.ebay.com",
        "trading": "https://api.sandbox.ebay.com/ws/api.dll",
    },
}

SCOPES = (
    "https://api.ebay.com/oauth/api_scope/sell.inventory "
    "https://api.ebay.com/oauth/api_scope/sell.account"
)


def _load_config():
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"{CONFIG_PATH} がありません。config.example.json をコピーして "
            "APIキー等を記入してください（SETUP_ebay_api.md 参照）。"
        )
    return json.loads(CONFIG_PATH.read_text())


class EbayClient:
    def __init__(self):
        self.cfg = _load_config()
        self.ep = ENDPOINTS[self.cfg.get("env", "production")]
        self._access_token = None
        self._expires_at = 0

    # ---- OAuth ----
    def access_token(self) -> str:
        """refresh_token から access_token を発行（キャッシュ有効ならそれを返す）。"""
        if self._access_token and time.time() < self._expires_at - 60:
            return self._access_token
        # ファイルキャッシュ確認
        if TOKEN_CACHE.exists():
            c = json.loads(TOKEN_CACHE.read_text())
            if time.time() < c.get("expires_at", 0) - 60:
                self._access_token = c["access_token"]
                self._expires_at = c["expires_at"]
                return self._access_token

        basic = base64.b64encode(
            f"{self.cfg['client_id']}:{self.cfg['client_secret']}".encode()
        ).decode()
        r = requests.post(
            self.ep["oauth"],
            headers={
                "Authorization": f"Basic {basic}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "grant_type": "refresh_token",
                "refresh_token": self.cfg["refresh_token"],
                "scope": SCOPES,
            },
            timeout=30,
        )
        r.raise_for_status()
        tok = r.json()
        self._access_token = tok["access_token"]
        self._expires_at = time.time() + tok.get("expires_in", 7200)
        TOKEN_CACHE.write_text(json.dumps(
            {"access_token": self._access_token, "expires_at": self._expires_at}))
        return self._access_token

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.access_token()}",
            "Content-Type": "application/json",
            "Content-Language": "en-US",
            "Accept-Language": "en-US",
        }

    # ---- Account API（ポリシーID取得・在庫ロケーション登録） ----
    def get_policies(self, kind: str):
        """kind: payment_policy / return_policy / fulfillment_policy。一覧を返す。"""
        r = requests.get(
            f'{self.ep["api"]}/sell/account/v1/{kind}',
            headers=self._headers(), params={"marketplace_id": "EBAY_US"}, timeout=30)
        r.raise_for_status()
        return r.json()

    def get_locations(self):
        r = requests.get(
            f'{self.ep["api"]}/sell/inventory/v1/location',
            headers=self._headers(), timeout=30)
        r.raise_for_status()
        return r.json()

    def create_location(self, key: str, address: dict):
        """在庫ロケーションを登録（初回のみ）。address例: {'city':'Nisshin','stateOrProvince':'Aichi','postalCode':'470-0111','country':'JP'}"""
        body = {
            "location": {"address": address},
            "locationInstructions": "Ships from Japan",
            "name": "noren-store Aichi",
            "merchantLocationStatus": "ENABLED",
            "locationTypes": ["WAREHOUSE"],
        }
        r = requests.post(
            f'{self.ep["api"]}/sell/inventory/v1/location/{key}',
            headers=self._headers(), json=body, timeout=30)
        if r.status_code not in (200, 201, 204):
            raise RuntimeError(f"location登録失敗 {r.status_code}: {r.text[:400]}")
        return True

    # ---- 写真アップロード（Trading API EPS） ----
    def upload_photo(self, image_path: Path) -> str:
        """ローカル画像を eBay Picture Service にアップロードし、ホストURLを返す。"""
        xml = f"""<?xml version="1.0" encoding="utf-8"?>
<UploadSiteHostedPicturesRequest xmlns="urn:ebay:apis:eBLBaseComponents">
  <RequesterCredentials><eBayAuthToken>{self.access_token()}</eBayAuthToken></RequesterCredentials>
  <PictureName>{image_path.stem}</PictureName>
</UploadSiteHostedPicturesRequest>"""
        files = {
            "XML Payload": (None, xml, "text/xml"),
            "image": (image_path.name, image_path.read_bytes(), "image/jpeg"),
        }
        headers = {
            "X-EBAY-API-COMPATIBILITY-LEVEL": "1193",
            "X-EBAY-API-CALL-NAME": "UploadSiteHostedPictures",
            "X-EBAY-API-SITEID": "0",
            "X-EBAY-API-IAF-TOKEN": self.access_token(),
        }
        r = requests.post(self.ep["trading"], headers=headers, files=files, timeout=60)
        r.raise_for_status()
        # XMLから FullURL を抽出（簡易）
        import re
        m = re.search(r"<FullURL>(.*?)</FullURL>", r.text)
        if not m:
            raise RuntimeError(f"画像URL取得失敗: {r.text[:400]}")
        return m.group(1)

    # ---- Inventory Item ----
    def put_inventory_item(self, sku, item: dict, image_urls=None):
        body = {
            "availability": {"shipToLocationAvailability": {"quantity": 1}},
            "condition": _cond_enum(item["ebay"].get("condition_id", "4000")),
            "product": {
                "title": item["title"][:80],
                "description": item["_html"],
                "aspects": item["ebay"].get("aspects", {}),
            },
        }
        if item["ebay"].get("condition_description"):
            body["conditionDescription"] = item["ebay"]["condition_description"]
        if image_urls:
            body["product"]["imageUrls"] = image_urls
        r = requests.put(
            f'{self.ep["api"]}/sell/inventory/v1/inventory_item/{sku}',
            headers=self._headers(), json=body, timeout=30)
        if r.status_code not in (200, 201, 204):
            raise RuntimeError(f"inventory_item失敗 {r.status_code}: {r.text[:500]}")
        return True

    # ---- Offer（未公開＝下書き） ----
    def create_offer(self, sku, item: dict) -> str:
        e = item["ebay"]
        body = {
            "sku": sku,
            "marketplaceId": "EBAY_US",
            "format": "FIXED_PRICE",
            "availableQuantity": 1,
            "categoryId": e["category_id"],
            "listingDescription": item["_html"],
            "listingPolicies": {
                "paymentPolicyId": self.cfg["payment_policy_id"],
                "returnPolicyId": self.cfg["return_policy_id"],
                "fulfillmentPolicyId": self.cfg["fulfillment_policy_id"],
            },
            "pricingSummary": {"price": {"value": str(e["price"]), "currency": "USD"}},
            "merchantLocationKey": self.cfg["merchant_location_key"],
        }
        if e.get("best_offer"):
            terms = {"bestOfferEnabled": True}
            if e.get("best_offer_min"):
                terms["autoDeclinePrice"] = {"value": str(e["best_offer_min"]), "currency": "USD"}
            body["listingPolicies"]["bestOfferTerms"] = terms
        r = requests.post(
            f'{self.ep["api"]}/sell/inventory/v1/offer',
            headers=self._headers(), json=body, timeout=30)
        if r.status_code not in (200, 201):
            raise RuntimeError(f"offer作成失敗 {r.status_code}: {r.text[:500]}")
        return r.json()["offerId"]

    def publish_offer(self, offer_id: str) -> str:
        r = requests.post(
            f'{self.ep["api"]}/sell/inventory/v1/offer/{offer_id}/publish',
            headers=self._headers(), timeout=30)
        if r.status_code not in (200, 201):
            raise RuntimeError(f"publish失敗 {r.status_code}: {r.text[:500]}")
        return r.json().get("listingId")


def _cond_enum(condition_id: str) -> str:
    """eBay condition_id → Inventory API の condition enum。"""
    return {
        "1000": "NEW",
        "2750": "LIKE_NEW",
        "4000": "USED_VERY_GOOD",
        "5000": "USED_GOOD",
        "6000": "USED_ACCEPTABLE",
    }.get(str(condition_id), "USED_VERY_GOOD")
