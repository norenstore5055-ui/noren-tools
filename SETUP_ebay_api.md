# eBay API セットアップ手順（Kojiさん本人作業）

出品自動化ツール（`list_item.py --draft`）を動かすには、eBayのAPIキーが必要です。
私（AI）はアカウント作成・認証情報入力はできないので、ここだけ手動でお願いします。**無料・15〜20分**です。

---

## STEP 1: eBay開発者アカウント登録
1. https://developer.ebay.com にアクセス
2. 右上「Register」→ **既存のnoren-store eBayアカウントでサインイン**して開発者登録（無料）
3. 開発者規約に同意

## STEP 2: アプリのキーセットを作成（Production）
1. ログイン後 **Develop → Your Keysets**（Application Keys）
2. **Production** の行で「Create a keyset」（本番。Sandboxは練習用なので今回は使わない）
3. 表示される3つを控える：
   - **App ID (Client ID)** → config.json の `client_id`
   - **Cert ID (Client Secret)** → config.json の `client_secret`
   - Dev ID（今回は未使用でOK）

## STEP 3: OAuthのRedirect URI (RuName) を作成
1. Production キーセットの「User Tokens」→「Get a Token from eBay via Your Application」
2. 「Add eBay Redirect URL」でRuNameを作成（accept/decline URLは任意のhttpsでOK。例 `https://example.com/accept`）
3. 生成された **RuName**（`Koji_...`みたいな文字列）→ config.json の `ru_name`

## STEP 4: 設定ファイルを用意
```bash
cd /Users/koji/Documents/CC/eBay/tools
cp config.example.json config.json
```
`config.json` を開いて STEP2/3 の値を記入。
（`client_id` `client_secret` `ru_name` の3つだけ先に埋めればOK。残りは下で取得）

## STEP 5: refresh_token を取得
```bash
python3 get_token.py
```
表示URLをブラウザ（noren-storeでログイン中）で開く→同意→リダイレクト先URLを貼り付け。
`refresh_token` が config.json に自動保存される。

## STEP 6: ポリシーID・在庫ロケーションを自動取得
```bash
python3 setup_account.py
```
Account APIから支払い/返品/配送ポリシーIDを取得してconfig.jsonに自動記入。
在庫ロケーションが無ければ Nisshin, Aichi で自動登録。**手入力不要。**

---

## 完了後の使い方
```bash
# HTML生成だけ（鍵不要・いつでも）
python3 list_item.py items/xxx.json

# eBay下書き作成（写真も自動UP）
python3 list_item.py items/xxx.json --draft --photos 9467-9475

# 下書き→即公開＋在庫追記
python3 list_item.py items/xxx.json --publish --photos 9467-9475 --cost 900
```

セットアップで詰まったら、エラーメッセージをそのまま貼ってください。一緒に解決します。
