import argparse
from pathlib import Path
from urllib.request import urlretrieve

import geopandas as gpd
from rich.console import Console
from rich.table import Table
from shapely.geometry import box

console = Console()

DATA_URL = "https://gtfs-gis.jp/railway_honsu/railway_honsu_2024.geojson"
CACHE_DIR = Path.home() / ".compare-regions-jp" / "data"
CACHE_FILE = CACHE_DIR / "railway_honsu_2024.geojson"


def download_and_cache_data() -> Path:
    """GeoJSONデータをダウンロードしてキャッシュする."""
    if CACHE_FILE.exists():
        return CACHE_FILE

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    console.print(f"[blue]データをダウンロード中: {DATA_URL}[/blue]")
    urlretrieve(DATA_URL, CACHE_FILE)
    console.print(f"[green]キャッシュに保存: {CACHE_FILE}[/green]")
    return CACHE_FILE


def load_railway_data() -> gpd.GeoDataFrame:
    """鉄道データを読み込む."""
    data_file = download_and_cache_data()
    return gpd.read_file(data_file)


def find_station(gdf: gpd.GeoDataFrame, station_name: str) -> gpd.GeoDataFrame:
    """指定された駅名の駅を検索する."""
    matches = gdf[gdf["駅名"] == station_name]
    if matches.empty:
        console.print(f"[bold red]エラー: 駅 '{station_name}' が見つかりません[/bold red]")
        exit(1)
    return matches


def calculate_bounding_box(
    lat: float, lon: float, width: float, height: float
) -> tuple[float, float, float, float]:
    """中心座標から境界ボックスを計算する."""
    minx = lon - width / 2
    maxx = lon + width / 2
    miny = lat - height / 2
    maxy = lat + height / 2
    return minx, miny, maxx, maxy


def count_stations_in_area(
    gdf: gpd.GeoDataFrame, bbox: tuple[float, float, float, float]
) -> int:
    """指定されたエリア内の駅の運行本数を集計する."""
    minx, miny, maxx, maxy = bbox
    area_box = box(minx, miny, maxx, maxy)
    stations_in_area = gdf[gdf.geometry.within(area_box)]

    total_trains = 0
    for _, station in stations_in_area.iterrows():
        train_count = station.get("本数", 0)
        if isinstance(train_count, int | float):
            total_trains += int(train_count)

    return total_trains


def display_comparison(
    station1_name: str,
    station1_coords: tuple[float, float],
    station1_trains: int,
    station2_name: str,
    station2_coords: tuple[float, float],
    station2_trains: int,
    width: float,
    height: float,
) -> None:
    """駅周辺エリアの比較結果を表示する."""
    table = Table(title="駅周辺エリア比較")
    table.add_column("項目", style="cyan")
    table.add_column(station1_name, style="green")
    table.add_column(station2_name, style="blue")

    table.add_row("緯度", f"{station1_coords[0]:.6f}", f"{station2_coords[0]:.6f}")
    table.add_row("経度", f"{station1_coords[1]:.6f}", f"{station2_coords[1]:.6f}")
    table.add_row("エリア幅(度)", f"{width}", f"{width}")
    table.add_row("エリア高さ(度)", f"{height}", f"{height}")
    table.add_row("総運行本数", f"{station1_trains}", f"{station2_trains}")

    diff = station1_trains - station2_trains
    diff_color = "green" if diff > 0 else "red" if diff < 0 else "white"
    table.add_row("差分", f"[{diff_color}]{diff:+d}[/{diff_color}]", "")

    console.print(table)


def main() -> None:
    """メイン処理."""
    parser = argparse.ArgumentParser(description="駅周辺エリアの運行本数を比較")
    parser.add_argument("-s1", "--station1", required=True, help="駅名1（必須）")
    parser.add_argument("-s2", "--station2", required=True, help="駅名2（必須）")
    parser.add_argument("-w", "--width", type=float, required=True, help="矩形幅（度、必須）")
    parser.add_argument("--height", type=float, required=True, help="矩形高さ（度、必須）")

    args = parser.parse_args()

    gdf = load_railway_data()

    station1_data = find_station(gdf, args.station1)
    station2_data = find_station(gdf, args.station2)

    station1_point = station1_data.geometry.iloc[0]
    station2_point = station2_data.geometry.iloc[0]

    station1_coords = (station1_point.y, station1_point.x)
    station2_coords = (station2_point.y, station2_point.x)

    bbox1 = calculate_bounding_box(
        station1_coords[0], station1_coords[1], args.width, args.height
    )
    bbox2 = calculate_bounding_box(
        station2_coords[0], station2_coords[1], args.width, args.height
    )

    station1_trains = count_stations_in_area(gdf, bbox1)
    station2_trains = count_stations_in_area(gdf, bbox2)

    display_comparison(
        args.station1,
        station1_coords,
        station1_trains,
        args.station2,
        station2_coords,
        station2_trains,
        args.width,
        args.height,
    )


if __name__ == "__main__":
    main()
