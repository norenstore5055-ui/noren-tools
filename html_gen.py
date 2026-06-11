"""
1商品JSON → noren-store標準出品HTMLを生成するジェネレーター。
これまで手書きしてきた構造（グラデヘッダー/推しボックス/Product Details表/
Condition/What's Included/Shipping/フッター）を完全踏襲する。

使い方:
  from html_gen import build_html
  html = build_html(item_dict)

item_dict のスキーマは tools/items/_schema.json を参照。
"""

import html as _html
import themes as _themes

FONT = "'Helvetica Neue',Arial,sans-serif"


def _esc(s: str) -> str:
    return _html.escape(str(s), quote=False)


def _details_rows(details: dict) -> str:
    rows = []
    for i, (k, v) in enumerate(details.items()):
        bg = ' style="background:#fff"' if i % 2 else ""
        rows.append(
            f'<tr{bg if i%2 else ""}>'
            f'<td style="padding:6px 12px;font-weight:bold;width:35%;color:#555">{_esc(k)}</td>'
            f'<td style="padding:6px 12px">{_esc(v)}</td></tr>'
            if i % 2 == 0 else
            f'<tr style="background:#fff">'
            f'<td style="padding:6px 12px;font-weight:bold;color:#555">{_esc(k)}</td>'
            f'<td style="padding:6px 12px">{_esc(v)}</td></tr>'
        )
    return "\n".join(rows)


def _li_list(items: list, allow_strong=True) -> str:
    out = []
    for it in items:
        # "Label: text" 形式なら Label を太字に
        if allow_strong and isinstance(it, str) and ":" in it and it.index(":") < 30:
            label, _, rest = it.partition(":")
            out.append(f'<li><strong>{_esc(label)}:</strong>{_esc(rest)}</li>')
        else:
            out.append(f'<li>{_esc(it)}</li>')
    return "\n".join(out)


def _warning_box(text: str) -> str:
    return (
        '<div style="background:#fff8e6;border:1px solid #e8d48a;border-radius:10px;'
        'padding:16px;margin-bottom:20px">\n'
        f'<p style="font-size:14px;margin:0">{text}</p>\n</div>\n\n'
    )


def build_html(item: dict) -> str:
    t = _themes.get(item.get("theme", _themes.DEFAULT))
    a = t["accent"]
    emoji = item.get("appeal_emoji", "")
    cross = item.get("shipping_crosssell",
                     "Combined shipping available — check out our other anime soundtrack and collectible listings!")

    parts = []
    parts.append(f'<div style="max-width:800px;margin:0 auto;font-family:{FONT};color:#333;line-height:1.6">\n')

    # ヘッダー
    parts.append(
        f'<div style="background:linear-gradient(135deg,{t["grad1"]},{t["grad2"]});'
        'padding:30px;border-radius:12px;text-align:center;margin-bottom:24px">\n'
        f'<h1 style="color:#fff;margin:0;font-size:22px;letter-spacing:1px">{_esc(item["title"])}</h1>\n'
        f'<p style="color:{t["sub"]};margin:8px 0 0;font-size:14px">{_esc(item["subtitle"])}</p>\n</div>\n\n'
    )

    # 推しボックス
    parts.append(
        f'<div style="background:{t["soft"]};border-radius:10px;padding:20px;margin-bottom:20px;'
        f'border:1px solid {t["border"]}">\n'
        f'<h2 style="font-size:16px;color:{a};margin:0 0 12px;border-bottom:2px solid {t["border"]};'
        f'padding-bottom:8px">{emoji} {_esc(item["appeal_heading"])}</h2>\n'
        f'<p style="font-size:14px;margin:0">{item["appeal_body"]}</p>\n</div>\n\n'
    )

    # Product Details
    parts.append(
        '<div style="background:#f8f9fa;border-radius:10px;padding:20px;margin-bottom:20px">\n'
        f'<h2 style="font-size:16px;color:{a};margin:0 0 12px;border-bottom:2px solid #e0e0e0;'
        'padding-bottom:8px">Product Details</h2>\n'
        '<table style="width:100%;border-collapse:collapse;font-size:14px">\n'
        f'{_details_rows(item["details"])}\n</table>\n</div>\n\n'
    )

    # 任意の注意書きボックス（日本語メニュー機/Untested等）
    if item.get("warning"):
        parts.append(_warning_box(item["warning"]))

    # Condition
    parts.append(
        '<div style="background:#f8f9fa;border-radius:10px;padding:20px;margin-bottom:20px">\n'
        f'<h2 style="font-size:16px;color:{a};margin:0 0 12px;border-bottom:2px solid #e0e0e0;'
        'padding-bottom:8px">Condition</h2>\n'
        f'<ul style="font-size:14px;margin:0;padding-left:20px">\n{_li_list(item["condition"])}\n</ul>\n'
        f'<p style="font-size:14px;margin:12px 0 0;color:{a}">Please see the photos for the exact item '
        f'you will receive — every angle is shown. {emoji}</p>\n</div>\n\n'
    )

    # What's Included
    parts.append(
        '<div style="background:#f8f9fa;border-radius:10px;padding:20px;margin-bottom:20px">\n'
        f'<h2 style="font-size:16px;color:{a};margin:0 0 12px;border-bottom:2px solid #e0e0e0;'
        'padding-bottom:8px">What\'s Included</h2>\n'
        f'<ul style="font-size:14px;margin:0;padding-left:20px">\n{_li_list(item["included"], allow_strong=False)}\n</ul>\n</div>\n\n'
    )

    # Shipping
    parts.append(
        '<div style="background:#f8f9fa;border-radius:10px;padding:20px;margin-bottom:20px">\n'
        f'<h2 style="font-size:16px;color:{a};margin:0 0 12px;border-bottom:2px solid #e0e0e0;'
        'padding-bottom:8px">Shipping</h2>\n'
        f'<p style="font-size:14px;margin:0">Ships from Aichi, Japan. Carefully packed in protective '
        f'material for safe international delivery. Tracking number provided. {cross}</p>\n</div>\n\n'
    )

    # フッター
    parts.append(
        '<div style="text-align:center;padding:16px;color:#888;font-size:12px;border-top:1px solid #eee;'
        'margin-top:20px">\n'
        '<p style="margin:0">Thank you for visiting <strong>noren-store</strong> — '
        'your gateway to authentic Japanese collectibles.</p>\n</div>\n\n</div>'
    )

    return "".join(parts)
