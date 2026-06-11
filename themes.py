"""
noren-store 出品HTMLのカラーテーマ定義。
各テーマ: (グラデ開始色, グラデ終了色, アクセント色, 淡い背景色, 枠線色)
これまで手書きしてきた14テンプレの配色を踏襲。
"""

THEMES = {
    # ピンク系（カードキャプターさくら等）
    "sakura":   {"grad1": "#d4607a", "grad2": "#f0a3b5", "accent": "#c2496a", "soft": "#fdf2f5", "border": "#f3cdd8", "sub": "#ffe3ea"},
    # 淡い青（エヴァ・レイ等）
    "paleblue": {"grad1": "#5b7fa6", "grad2": "#a8c4dd", "accent": "#3d5a78", "soft": "#f0f5fa", "border": "#c9dcec", "sub": "#e8f1f8"},
    # 青空（エヴァDEATH等）
    "sky":      {"grad1": "#1e3a6e", "grad2": "#5b7fb8", "accent": "#1e3a6e", "soft": "#eef3fb", "border": "#c6d6ee", "sub": "#dde8f5"},
    # 紫（サクラ大戦等）
    "purple":   {"grad1": "#7a4988", "grad2": "#c98bc9", "accent": "#6b3d78", "soft": "#f9f2fa", "border": "#e3cce6", "sub": "#f0dff0"},
    # ゴールド（ナデシコOST3等）
    "gold":     {"grad1": "#a8842c", "grad2": "#e0c068", "accent": "#8a6d1f", "soft": "#fbf6e8", "border": "#e8d9a8", "sub": "#f7edd2"},
    # 緑星空（ナデシコCD-001等）
    "green":    {"grad1": "#2e5e3a", "grad2": "#7aa86b", "accent": "#36603f", "soft": "#eef5ec", "border": "#c8dec0", "sub": "#e3f0dd"},
    # ジブリ緑（耳をすませば等）
    "ghibli":   {"grad1": "#4a7c59", "grad2": "#a3c9a8", "accent": "#3d6849", "soft": "#eff7f0", "border": "#c9e0cd", "sub": "#e8f3ea"},
    # ワインレッド（マクロスF等）
    "wine":     {"grad1": "#8c4a5e", "grad2": "#d9a0ae", "accent": "#7d3c4f", "soft": "#faf0f3", "border": "#ecccd5", "sub": "#f6e4e9"},
    # 深紅（エヴァ終劇等）
    "crimson":  {"grad1": "#7a1212", "grad2": "#c43c3c", "accent": "#8c1f1f", "soft": "#fdf0f0", "border": "#ecc3c3", "sub": "#f5dada"},
    # サイバーパンク黒×ピンク（スナッチャー パイロット盤等）
    "cyber":    {"grad1": "#1a1a2e", "grad2": "#c2185b", "accent": "#9c2a5b", "soft": "#fdf1f6", "border": "#ecc6d8", "sub": "#f3d4e2"},
    # ブラウン（スナッチャー本編等）
    "brown":    {"grad1": "#3d2b1f", "grad2": "#b3541e", "accent": "#8c4a1d", "soft": "#fdf5ee", "border": "#e8cdb3", "sub": "#f5e3d3"},
}

DEFAULT = "paleblue"


def get(name: str) -> dict:
    return THEMES.get(name, THEMES[DEFAULT])
