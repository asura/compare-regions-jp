# compare-regions-jp

日本の地域を複数観点から比較し、差異をレポートするCLIツール

## 🚀 使用方法

### インストール
```bash
git clone https://github.com/asura/compare-regions-jp.git
cd compare-regions-jp
poetry install
```

### 基本的な使い方
```bash
# 基本コマンド
python -m compare_regions_jp.cli -s1 渋谷 -s2 有楽町 --width 0.016 --height 0.015

# ヘルプ表示
python -m compare_regions_jp.cli --help
```

### コマンドオプション
- `-s1, --station1`: 1つ目の駅名（完全一致、必須）
- `-s2, --station2`: 2つ目の駅名（完全一致、必須）
- `-w, --width`: 矩形幅（度単位、必須）
- `--height`: 矩形高さ（度単位、必須）

### 実行例
```bash
# 渋谷駅と新宿駅周辺の鉄道運行本数を比較
python -m compare_regions_jp.cli -s1 渋谷 -s2 新宿 --width 0.016 --height 0.015

# 東京駅と品川駅周辺を比較（少し広めの範囲）
python -m compare_regions_jp.cli -s1 東京 -s2 品川 --width 0.020 --height 0.018
```

### 出力例
```
🚉 駅情報
渋谷駅: 35.658, 139.702
有楽町駅: 35.675, 139.763

📊 鉄道運行本数比較
┏━━━━━━━━━━━━━┳━━━━━━━━━━━━━┓
┃ エリア      ┃ 運行本数/日 ┃
┡━━━━━━━━━━━━━╇━━━━━━━━━━━━━┩
│ 渋谷駅エリア │ 2,847本     │
│ 有楽町駅エリア │ 1,923本     │
└─────────────┴─────────────┘

✅ 渋谷駅エリアの方が924本/日多い
```

### 注意事項
- 初回実行時にデータを自動ダウンロードします
- 駅名は完全一致で検索されます
- 矩形サイズの目安: 0.016×0.015度 ≈ 徒歩10分圏
