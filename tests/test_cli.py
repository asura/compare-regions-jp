from pathlib import Path
from unittest.mock import Mock, patch

import geopandas as gpd
import pytest
from compare_regions_jp.cli import (
    calculate_bounding_box,
    count_stations_in_area,
    display_comparison,
    download_and_cache_data,
    find_station,
    load_railway_data,
    main,
)
from shapely.geometry import Point


def describe_データ管理():
    def describe_キャッシュ機能():
        @patch("compare_regions_jp.cli.CACHE_FILE")
        @patch("compare_regions_jp.cli.urlretrieve")
        def 初回ダウンロード時にキャッシュファイルを作成(mock_urlretrieve, mock_cache_file):
            mock_cache_file.exists.return_value = False
            mock_cache_file.parent.mkdir = Mock()

            download_and_cache_data()

            mock_urlretrieve.assert_called_once()

        @patch("compare_regions_jp.cli.CACHE_FILE")
        def キャッシュファイルが存在する場合はダウンロードしない(mock_cache_file):
            mock_cache_file.exists.return_value = True

            result = download_and_cache_data()

            assert result == mock_cache_file


def describe_駅検索():
    def 完全一致検索で駅が見つかる():
        gdf = gpd.GeoDataFrame(
            {
                "駅名": ["東京", "新宿", "渋谷"],
                "geometry": [
                    Point(139.7, 35.7),
                    Point(139.7, 35.7),
                    Point(139.7, 35.7),
                ],
            }
        )

        result = find_station(gdf, "東京")

        assert len(result) == 1
        assert result.iloc[0]["駅名"] == "東京"

    def 存在しない駅名でエラー終了():
        gdf = gpd.GeoDataFrame(
            {"駅名": ["東京", "新宿"], "geometry": [Point(139.7, 35.7), Point(139.7, 35.7)]}
        )

        with pytest.raises(SystemExit):
            find_station(gdf, "存在しない駅")


def describe_矩形計算():
    def 中心座標から正しい境界ボックスを計算():
        lat, lon = 35.0, 139.0
        width, height = 0.1, 0.1

        minx, miny, maxx, maxy = calculate_bounding_box(lat, lon, width, height)

        assert minx == 138.95
        assert maxx == 139.05
        assert miny == 34.95
        assert maxy == 35.05


def describe_本数集計():
    def エリア内駅の運行本数を正しく合計():
        gdf = gpd.GeoDataFrame(
            {
                "駅名": ["A駅", "B駅", "C駅"],
                "着数1": [10, 20, 5],
                "発数1": [15, 25, 10],
                "着数2": [30, 40, 15],
                "発数2": [45, 115, 20],
                "geometry": [
                    Point(139.0, 35.0),  # エリア内
                    Point(139.01, 35.01),  # エリア内
                    Point(140.0, 36.0),  # エリア外
                ],
            }
        )
        bbox = (138.99, 34.99, 139.02, 35.02)

        arrivals, departures, total = count_stations_in_area(gdf, bbox)

        # A駅: 着=10+30=40, 発=15+45=60, 計=100
        # B駅: 着=20+40=60, 発=25+115=140, 計=200
        # C駅: エリア外
        assert arrivals == 100  # 40 + 60
        assert departures == 200  # 60 + 140
        assert total == 300  # 100 + 200

    def 本数データがない場合は0として扱う():
        gdf = gpd.GeoDataFrame({"駅名": ["A駅"], "geometry": [Point(139.0, 35.0)]})
        bbox = (138.99, 34.99, 139.01, 35.01)

        arrivals, departures, total = count_stations_in_area(gdf, bbox)

        assert arrivals == 0
        assert departures == 0
        assert total == 0


def describe_CLI():
    @patch("compare_regions_jp.cli.load_railway_data")
    def 必須引数が全て提供された場合に正常実行(mock_load_data):
        mock_gdf = gpd.GeoDataFrame(
            {"駅名": ["東京", "新宿"], "geometry": [Point(139.7, 35.7), Point(139.7, 35.7)]}
        )
        mock_load_data.return_value = mock_gdf

        with patch(
            "sys.argv",
            ["cli.py", "-s1", "東京", "-s2", "新宿", "-w", "0.1", "--height", "0.1"],
        ):
            with patch("compare_regions_jp.cli.display_comparison"):
                main()

    def 必須引数不足でヘルプ表示():
        with patch("sys.argv", ["cli.py"]):
            with pytest.raises(SystemExit):
                main()


def describe_ダウンロード():
    @patch("compare_regions_jp.cli.CACHE_FILE")
    @patch("compare_regions_jp.cli.console")
    def ダウンロード時にメッセージ表示(mock_console, mock_cache_file):
        mock_cache_file.exists.return_value = False

        with patch("compare_regions_jp.cli.urlretrieve"):
            download_and_cache_data()

        assert mock_console.print.call_count == 2

    @patch("compare_regions_jp.cli.download_and_cache_data")
    def データファイル読み込み(mock_download):
        mock_download.return_value = Path("/tmp/test.geojson")

        with patch("geopandas.read_file") as mock_read:
            load_railway_data()
            mock_read.assert_called_once()


def describe_表示():
    @patch("compare_regions_jp.cli.console")
    def 比較結果を正しく表示(mock_console):
        display_comparison(
            "東京",
            (35.7, 139.7),
            (40, 60, 100),
            "新宿",
            (35.7, 139.7),
            (30, 50, 80),
            0.1,
            0.1,
        )

        mock_console.print.assert_called_once()
