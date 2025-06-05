# Claude Code 開発ガイド

## 🎯 プロジェクト概要

compare-regions-jp は日本の地域比較CLIツールです。Claude Code による自動開発を前提とした設計になっています。

## 🏗️ アーキテクチャ原則

### 1. 単一責任の原則
- 各クラスは1つの明確な役割を持つ
- Region クラス: 地域境界管理
- Metric クラス: 指標計算
- Reporter クラス: レポート生成

### 2. 依存性の方向
```
CLI → Core → Data
     ↓      ↓
   Output ← Metrics
```

### 3. エラーハンドリング
- カスタム例外使用: `RegionNotFoundError`, `DataSourceError`
- Rich Console でユーザフレンドリーな表示
- ログレベル: DEBUG, INFO, WARNING, ERROR

## 📁 ディレクトリ構造と役割

```
src/compare_regions_jp/
├── __init__.py          # バージョン情報
├── cli.py               # CLIエントリーポイント
├── config.py            # 設定・定数定義
├── exceptions.py        # カスタム例外
├── core/                # ビジネスロジック
│   ├── __init__.py
│   ├── region.py        # Region クラス（地域定義・境界取得）
│   └── metrics/         # 指標計算モジュール
│       ├── __init__.py
│       ├── base.py      # Metric 抽象基底クラス
│       ├── poi.py       # POI件数指標
│       └── density.py   # 密度系指標
├── data/                # 外部データ取得・キャッシュ
│   ├── __init__.py
│   ├── cache.py         # キャッシュ管理
│   ├── geocoding.py     # ジオコーディング
│   └── osm.py          # OSMデータ取得
└── output/              # レポート生成
    ├── __init__.py
    ├── markdown.py      # Markdownレポート
    └── json_export.py   # JSON出力
```

## 🎨 コーディング規約

### 命名規則
```python
# クラス: PascalCase
class POICountMetric:
    pass

# 関数・変数: snake_case
def calculate_poi_count(region: Region) -> int:
    poi_data = fetch_poi_data()
    return len(poi_data)

# 定数: UPPER_CASE
DEFAULT_WALK_MINUTES = 10
API_TIMEOUT_SECONDS = 30

# ファイル: snake_case
# poi_metric.py, region_parser.py
```

### 型ヒント
```python
# 必須: 全ての関数に型ヒント
def process_region(region: Region) -> ProcessResult:
    ...

# Optional/Union の使用
from typing import Optional, Union, List, Dict

def get_cached_data(key: str) -> Optional[Dict[str, Any]]:
    ...
```

### docstring
```python
def calculate_metric(region: Region, metric_type: str) -> MetricResult:
    """指定された地域の指標を計算する.

    Args:
        region: 計算対象の地域
        metric_type: 指標タイプ（'poi_count', 'intersection_density' など）

    Returns:
        計算結果を含むMetricResultオブジェクト

    Raises:
        RegionNotFoundError: 地域境界が取得できない場合
        DataSourceError: データソースへのアクセスに失敗した場合
    """
```

## 🧪 テストパターン

### テストファイル構造
```
tests/
├── __init__.py
├── conftest.py          # pytest fixtures
├── test_cli.py          # CLI機能テスト
├── core/
│   ├── test_region.py   # Region クラステスト
│   └── metrics/
│       └── test_poi.py  # POI指標テスト
├── data/
│   └── test_cache.py    # キャッシュ機能テスト
├── output/
│   └── test_markdown.py # レポート生成テスト
└── fixtures/            # テストデータ
    ├── sample_regions.json
    └── sample_poi_data.json
```

### テストケース設計
各機能について以下の3パターンを必ず実装：

```python
# 1. 正常系テスト
def test_poi_count_success():
    """正常なPOI取得のテスト"""
    
# 2. 異常系テスト  
def test_poi_count_network_error():
    """ネットワークエラー時のテスト"""
    
# 3. 境界値テスト
def test_poi_count_empty_region():
    """空の地域での動作テスト"""
```

### モック使用
外部API呼び出しは必ずモック化：

```python
@patch('requests.get')
def test_osm_api_call(mock_get):
    mock_get.return_value.json.return_value = SAMPLE_OSM_DATA
    # テスト実装
```

## 🔧 開発ワークフロー

### 1. 機能実装の流れ
1. **GitHub Issue確認** - 実装要求・仕様を理解
2. **テスト作成** - TDD: テストファースト
3. **実装** - 最小限の動作する実装
4. **リファクタリング** - コード品質向上
5. **ドキュメント更新** - docstring, README更新

### 2. コミット前チェック
```bash
# 自動実行される項目
poetry run black src/ tests/     # フォーマット
poetry run ruff check src/ tests/  # リント
poetry run mypy src/             # 型チェック  
poetry run pytest               # テスト実行
```

### 3. PR作成時
- [ ] 全テスト通過
- [ ] カバレッジ85%以上
- [ ] 型チェック通過
- [ ] docstring記述完了

## 🚀 Claude Code への指示例

### ✅ 良い指示
```
Issue #5対応: POI取得機能を実装してください

【実装仕様】
- ファイル: src/compare_regions_jp/data/poi.py
- クラス: POIFetcher
- メソッド: fetch_pois(region: Region) -> List[POI]
- API: OSM Overpass、10秒タイムアウト
- キャッシュ: joblib使用、TTL 24時間

【テスト要求】
- ファイル: tests/data/test_poi.py
- 正常系: 成功時のPOI取得
- 異常系: タイムアウト、ネットワークエラー
- モック: Overpass APIレスポンス

【品質基準】
- カバレッジ85%以上
- mypy strict通過
- docstring完備
```

### ❌ 避けるべき指示
```
POI機能作って
```

## 📊 品質メトリクス

### 自動チェック項目
- **テストカバレッジ**: 85%以上
- **型チェック**: mypy strict mode 通過
- **リント**: ruff チェック通過  
- **フォーマット**: black 統一

### 手動レビュー項目
- **アーキテクチャ整合性**: 依存関係の方向性
- **エラーハンドリング**: 適切な例外処理
- **ユーザビリティ**: CLI使用感
- **パフォーマンス**: 応答時間

## 🔍 デバッグ・トラブルシューティング

### ログ出力
```python
import logging
from rich.logging import RichHandler

# 推奨ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler()]
)

logger = logging.getLogger("compare_regions_jp")
```

### 典型的な問題と解決策

#### 地理空間ライブラリエラー
```bash
# GDAL関連エラー
sudo apt-get install gdal-bin libgdal-dev

# Shapely エラー  
poetry add shapely --extras proj
```

#### テスト実行エラー
```bash
# キャッシュクリア
rm -rf .pytest_cache __pycache__

# 依存関係再インストール
poetry install --no-cache
```

## 📚 参考資料

### 外部API
- [OSM Overpass API](https://wiki.openstreetmap.org/wiki/Overpass_API)
- [Nominatim API](https://nominatim.org/release-docs/develop/api/Overview/)

### Python ライブラリ
- [Click Documentation](https://click.palletsprojects.com/)
- [Rich Documentation](https://rich.readthedocs.io/)
- [GeoPandas User Guide](https://geopandas.org/en/stable/docs.html)
- [OSMnx Documentation](https://osmnx.readthedocs.io/)

### 開発ツール
- [pytest Documentation](https://docs.pytest.org/)
- [Black Code Style](https://black.readthedocs.io/)
- [Ruff Rules](https://docs.astral.sh/ruff/rules/)