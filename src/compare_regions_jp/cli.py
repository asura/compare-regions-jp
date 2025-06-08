import click
import geopandas as gpd
from rich.console import Console
from rich.table import Table
from shapely.geometry import box

from compare_regions_jp.data.railway import RailwayDataLoader

console = Console()


def load_railway_data() -> gpd.GeoDataFrame:
    """鉄道データを読み込む."""
    loader = RailwayDataLoader()
    result = loader.load_railway_data()

    if result.data is None:
        console.print("[bold red]エラー: 鉄道データの取得に失敗しました[/bold red]")
        exit(1)

    # デバッグ情報表示
    if result.cached:
        console.print(f"[dim]キャッシュから取得 ({result.load_time_seconds:.2f}秒)[/dim]")
    else:
        console.print(f"[dim]データダウンロード完了 ({result.load_time_seconds:.2f}秒)[/dim]")

    return result.data


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
) -> tuple[int, int, int]:
    """指定されたエリア内の駅の運行本数を集計する."""
    minx, miny, maxx, maxy = bbox
    area_box = box(minx, miny, maxx, maxy)
    stations_in_area = gdf[gdf.geometry.within(area_box)]

    total_arrivals = 0
    total_departures = 0
    for _, station in stations_in_area.iterrows():
        arrivals1 = station.get("着数1", 0)
        departures1 = station.get("発数1", 0)
        arrivals2 = station.get("着数2", 0)
        departures2 = station.get("発数2", 0)

        # 数値型でない場合は0として扱う
        arrivals1 = int(arrivals1) if isinstance(arrivals1, int | float) else 0
        departures1 = int(departures1) if isinstance(departures1, int | float) else 0
        arrivals2 = int(arrivals2) if isinstance(arrivals2, int | float) else 0
        departures2 = int(departures2) if isinstance(departures2, int | float) else 0

        total_arrivals += arrivals1 + arrivals2
        total_departures += departures1 + departures2

    total_trains = total_arrivals + total_departures
    return total_arrivals, total_departures, total_trains


def show_about_info() -> None:
    """データソース・ライセンス情報を表示"""
    console.print("📊 [bold]Compare Regions JP[/bold]")
    console.print("2駅周辺エリアの鉄道運行本数比較ツール\n")

    console.print("📄 [bold]データソース[/bold]")
    console.print("• データ名: 路線別・駅別発着本数データ2024")
    console.print("• 提供元: GTFS-GIS.jp")
    console.print("• URL: https://gtfs-gis.jp/railway_honsu/")
    console.print("• ライセンス: CC BY 4.0, ODbL")
    console.print()

    console.print("🙏 [bold]謝辞[/bold]")
    console.print("素晴らしいオープンデータを提供いただいている")
    console.print("西澤先生をはじめとするGTFS-GIS.jpの関係者の皆様に")
    console.print("深く感謝申し上げます。")
    console.print()

    console.print("⚖️  [bold]ライセンス条項[/bold]")
    console.print("• CC BY 4.0: データの利用・改変・再配布可能（著作者クレジット表示必須）")
    console.print("• ODbL: データベースの利用・改変・再配布可能（同ライセンス提供必須）")
    console.print()

    console.print("🔗 詳細: https://gtfs-gis.jp/railway_honsu/")


def display_comparison(
    station1_name: str,
    station1_coords: tuple[float, float],
    station1_trains: tuple[int, int, int],
    station2_name: str,
    station2_coords: tuple[float, float],
    station2_trains: tuple[int, int, int],
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

    station1_arrivals, station1_departures, station1_total = station1_trains
    station2_arrivals, station2_departures, station2_total = station2_trains

    table.add_row("到着本数", f"{station1_arrivals}", f"{station2_arrivals}")
    table.add_row("出発本数", f"{station1_departures}", f"{station2_departures}")
    table.add_row("総運行本数", f"{station1_total}", f"{station2_total}")

    diff = station1_total - station2_total
    diff_color = "green" if diff > 0 else "red" if diff < 0 else "white"
    table.add_row("差分", f"[{diff_color}]{diff:+d}[/{diff_color}]", "")

    console.print(table)


@click.command()
@click.option("-s1", "--station1", help="1つ目の駅名（完全一致）")
@click.option("-s2", "--station2", help="2つ目の駅名（完全一致）")
@click.option("-w", "--width", type=float, help="矩形幅（度単位）")
@click.option("-h", "--height", type=float, help="矩形高さ（度単位）")
@click.option("--about", is_flag=True, help="データソース・ライセンス情報を表示")
def main(
    station1: str | None,
    station2: str | None,
    width: float | None,
    height: float | None,
    about: bool,
) -> None:
    """2駅周辺エリアの鉄道運行本数を比較"""
    if about:
        show_about_info()
        return

    # --aboutオプション以外では必須チェック
    if not station1 or not station2 or width is None or height is None:
        console.print("[bold red]エラー: -s1, -s2, -w, -h は必須です[/bold red]")
        console.print(
            "使用方法: python -m compare_regions_jp.cli -s1 駅名1 -s2 駅名2 -w 幅 -h 高さ"
        )
        console.print("ヘルプ: python -m compare_regions_jp.cli --help")
        console.print("情報表示: python -m compare_regions_jp.cli --about")
        exit(1)

    gdf = load_railway_data()

    station1_data = find_station(gdf, station1)
    station2_data = find_station(gdf, station2)

    station1_point = station1_data.geometry.iloc[0]
    station2_point = station2_data.geometry.iloc[0]

    station1_coords = (station1_point.y, station1_point.x)
    station2_coords = (station2_point.y, station2_point.x)

    bbox1 = calculate_bounding_box(
        station1_coords[0], station1_coords[1], width, height
    )
    bbox2 = calculate_bounding_box(
        station2_coords[0], station2_coords[1], width, height
    )

    station1_trains = count_stations_in_area(gdf, bbox1)
    station2_trains = count_stations_in_area(gdf, bbox2)

    display_comparison(
        station1,
        station1_coords,
        station1_trains,
        station2,
        station2_coords,
        station2_trains,
        width,
        height,
    )


if __name__ == "__main__":
    main()
