"""鉄道データローダーのテスト。"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch
from urllib.error import URLError

import geopandas as gpd
import pytest
from compare_regions_jp.data.base import CacheError, DataLoadError
from compare_regions_jp.data.railway import RailwayDataLoader
from shapely.geometry import Point

# テストデータ
SAMPLE_RAILWAY_DATA = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "properties": {"駅名": "渋谷", "着数1": 100, "発数1": 102},
            "geometry": {"type": "Point", "coordinates": [139.7016, 35.6580]},
        },
        {
            "type": "Feature",
            "properties": {"駅名": "新宿", "着数1": 150, "発数1": 155},
            "geometry": {"type": "Point", "coordinates": [139.7004, 35.6896]},
        },
    ],
}


class TestRailwayDataLoader:
    """鉄道データローダーのテストクラス。"""

    def test_init(self):
        """初期化のテスト。"""
        loader = RailwayDataLoader()
        assert loader.cache_enabled is True
        assert (
            loader.data_url
            == "https://gtfs-gis.jp/railway_honsu/data/unkohonsu2024_rosen_eki.geojson"
        )

    def test_init_cache_disabled(self):
        """キャッシュ無効での初期化のテスト。"""
        loader = RailwayDataLoader(cache_enabled=False)
        assert loader.cache_enabled is False

    @patch("compare_regions_jp.data.railway.urlretrieve")
    @patch("compare_regions_jp.data.railway.gpd.read_file")
    def test_load_data_from_source_success(self, mock_read_file, mock_urlretrieve):
        """ソースからのデータロード成功のテスト。"""
        # モック設定
        mock_gdf = gpd.GeoDataFrame(
            [
                {
                    "駅名": "渋谷",
                    "着数1": 100,
                    "発数1": 102,
                    "geometry": Point(139.7016, 35.6580),
                },
                {
                    "駅名": "新宿",
                    "着数1": 150,
                    "発数1": 155,
                    "geometry": Point(139.7004, 35.6896),
                },
            ]
        )
        mock_read_file.return_value = mock_gdf

        loader = RailwayDataLoader()
        result = loader._load_data_from_source("https://example.com/data.geojson")

        # 検証
        assert isinstance(result, gpd.GeoDataFrame)
        assert len(result) == 2
        mock_urlretrieve.assert_called_once()
        mock_read_file.assert_called_once()

    @patch("compare_regions_jp.data.railway.urlretrieve")
    def test_load_data_from_source_network_error(self, mock_urlretrieve):
        """ネットワークエラーのテスト。"""
        mock_urlretrieve.side_effect = URLError("Network error")

        loader = RailwayDataLoader()
        with pytest.raises(DataLoadError) as exc_info:
            loader._load_data_from_source("https://example.com/data.geojson")

        assert "鉄道データの取得に失敗しました" in str(exc_info.value)

    @patch("compare_regions_jp.data.railway.urlretrieve")
    @patch("compare_regions_jp.data.railway.gpd.read_file")
    def test_load_data_from_source_with_bbox(self, mock_read_file, mock_urlretrieve):
        """bboxフィルタリングのテスト。"""
        # 元のGeoDataFrame（bbox外の駅も含む）
        mock_gdf = gpd.GeoDataFrame(
            [
                {
                    "駅名": "渋谷",
                    "着数1": 100,
                    "発数1": 102,
                    "geometry": Point(139.7016, 35.6580),
                },
                {
                    "駅名": "新宿",
                    "着数1": 150,
                    "発数1": 155,
                    "geometry": Point(139.7004, 35.6896),
                },
                {
                    "駅名": "遠い駅",
                    "着数1": 50,
                    "発数1": 55,
                    "geometry": Point(140.0000, 36.0000),
                },  # bbox外
            ]
        )
        mock_read_file.return_value = mock_gdf

        loader = RailwayDataLoader()
        bbox = (139.69, 35.65, 139.71, 35.70)
        result = loader._load_data_from_source(
            "https://example.com/data.geojson", bbox=bbox
        )

        # 検証：データが読み込まれることを確認（実際のフィルタリングはGeoPandasの機能に依存）
        assert isinstance(result, gpd.GeoDataFrame)
        mock_urlretrieve.assert_called_once()
        mock_read_file.assert_called_once()

    def test_save_to_cache(self):
        """キャッシュ保存のテスト。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_path = Path(temp_dir) / "test_cache.geojson"

            # テストデータ作成
            gdf = gpd.GeoDataFrame(
                [
                    {
                        "駅名": "渋谷",
                        "着数1": 100,
                        "発数1": 102,
                        "geometry": Point(139.7016, 35.6580),
                    }
                ]
            )

            loader = RailwayDataLoader()
            loader._save_to_cache(gdf, cache_path)

            # 検証
            assert cache_path.exists()
            loaded_gdf = gpd.read_file(cache_path)
            assert len(loaded_gdf) == 1
            assert loaded_gdf.iloc[0]["駅名"] == "渋谷"

    def test_save_to_cache_error(self):
        """キャッシュ保存エラーのテスト。"""
        # 存在しないディレクトリのパス
        cache_path = Path("/nonexistent/path/cache.geojson")

        gdf = gpd.GeoDataFrame(
            [{"駅名": "渋谷", "着数1": 100, "発数1": 102, "geometry": Point(139.7016, 35.6580)}]
        )

        loader = RailwayDataLoader()
        with pytest.raises(CacheError) as exc_info:
            loader._save_to_cache(gdf, cache_path)

        assert "キャッシュ保存に失敗しました" in str(exc_info.value)

    def test_load_from_cache(self):
        """キャッシュ読み込みのテスト。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_path = Path(temp_dir) / "test_cache.geojson"

            # テストデータをファイルに保存
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(SAMPLE_RAILWAY_DATA, f, ensure_ascii=False)

            loader = RailwayDataLoader()
            result = loader._load_from_cache(cache_path)

            # 検証
            assert isinstance(result, gpd.GeoDataFrame)
            assert len(result) == 2
            assert result.iloc[0]["駅名"] == "渋谷"
            assert result.iloc[1]["駅名"] == "新宿"

    def test_load_from_cache_error(self):
        """キャッシュ読み込みエラーのテスト。"""
        # 存在しないファイル
        cache_path = Path("/nonexistent/file.geojson")

        loader = RailwayDataLoader()
        with pytest.raises(CacheError) as exc_info:
            loader._load_from_cache(cache_path)

        assert "キャッシュ読み込みに失敗しました" in str(exc_info.value)

    @patch("compare_regions_jp.data.railway.urlretrieve")
    @patch("compare_regions_jp.data.railway.gpd.read_file")
    def test_load_railway_data_integration(self, mock_read_file, mock_urlretrieve):
        """load_railway_dataメソッドの統合テスト。"""
        mock_gdf = gpd.GeoDataFrame(
            [{"駅名": "渋谷", "着数1": 100, "発数1": 102, "geometry": Point(139.7016, 35.6580)}]
        )
        mock_read_file.return_value = mock_gdf

        loader = RailwayDataLoader(cache_enabled=False)  # キャッシュ無効でテスト
        result = loader.load_railway_data()

        # 検証
        assert result.data is not None
        assert isinstance(result.data, gpd.GeoDataFrame)
        assert result.cached is False
        assert result.load_time_seconds >= 0

    @patch("compare_regions_jp.data.railway.urlretrieve")
    @patch("compare_regions_jp.data.railway.gpd.read_file")
    def test_load_railway_data_with_bbox(self, mock_read_file, mock_urlretrieve):
        """bboxありでのload_railway_dataメソッドのテスト。"""
        mock_gdf = gpd.GeoDataFrame(
            [{"駅名": "渋谷", "着数1": 100, "発数1": 102, "geometry": Point(139.7016, 35.6580)}]
        )
        mock_read_file.return_value = mock_gdf

        loader = RailwayDataLoader(cache_enabled=False)
        bbox = (139.69, 35.65, 139.71, 35.70)
        result = loader.load_railway_data(bbox=bbox)

        # 検証
        assert result.data is not None
        assert isinstance(result.data, gpd.GeoDataFrame)
        mock_urlretrieve.assert_called_once()
        mock_read_file.assert_called_once()
