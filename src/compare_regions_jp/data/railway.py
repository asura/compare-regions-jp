"""鉄道データローダー。

GTFS-GIS.jpから鉄道運行本数データを取得し、統一されたキャッシュ機能を提供する。
"""

import tempfile
from pathlib import Path
from typing import Any
from urllib.request import urlretrieve

import geopandas as gpd
from rich.console import Console

from compare_regions_jp.data.base import BaseDataLoader, CacheError, DataLoadError


class RailwayDataLoader(BaseDataLoader):
    """鉄道データローダー。

    GTFS-GIS.jpから鉄道運行本数データを取得し、
    指定されたbounding boxでフィルタリングする。
    """

    def __init__(self, cache_enabled: bool = True):
        """鉄道データローダーを初期化。

        Args:
        ----
            cache_enabled: キャッシュ機能の有効/無効

        """
        super().__init__(cache_enabled=cache_enabled)
        self.data_url = (
            "https://gtfs-gis.jp/railway_honsu/data/unkohonsu2024_rosen_eki.geojson"
        )
        self.console = Console()

    def load_railway_data(
        self, bbox: tuple[float, float, float, float] | None = None
    ) -> Any:
        """鉄道データを読み込む。

        Args:
        ----
            bbox: フィルタリング用の境界ボックス (minx, miny, maxx, maxy)
                 Noneの場合は全データを取得

        Returns:
        -------
            鉄道データのロード結果（DataLoadResult）

        """
        source = f"{self.data_url}?bbox={bbox}" if bbox else self.data_url
        return self.load_data(source, bbox=bbox)

    def _load_data_from_source(self, source: str, **kwargs: Any) -> gpd.GeoDataFrame:
        """ソースから鉄道データを直接ロード。

        Args:
        ----
            source: データソース（URL）
            **kwargs: 追加パラメータ（bbox等）

        Returns:
        -------
            鉄道データのGeoDataFrame

        Raises:
        ------
            DataLoadError: データロードに失敗した場合

        """
        try:
            # ライセンス情報とダウンロード状況を表示
            self.console.print("📄 データライセンス: CC BY 4.0, ODbL")
            self.console.print("📍 データ提供: GTFS-GIS.jp")
            self.console.print(f"⬇️  鉄道運行本数データをダウンロード中: {self.data_url}")

            # 一時ファイルにダウンロード
            with tempfile.NamedTemporaryFile(
                suffix=".geojson", delete=False
            ) as temp_file:
                temp_path = Path(temp_file.name)

            try:
                urlretrieve(self.data_url, temp_path)

                # GeoDataFrameとして読み込み
                gdf = gpd.read_file(temp_path)

                # bboxフィルタリング
                bbox = kwargs.get("bbox")
                if bbox is not None:
                    minx, miny, maxx, maxy = bbox
                    # 境界ボックス内のデータのみフィルタリング
                    gdf = gdf.cx[minx:maxx, miny:maxy]

                return gdf

            finally:
                # 一時ファイルを削除
                if temp_path.exists():
                    temp_path.unlink()

        except Exception as e:
            raise DataLoadError(
                f"鉄道データの取得に失敗しました: {e}", source, original_error=e
            ) from e

    def _save_to_cache(self, data: gpd.GeoDataFrame, cache_path: Path) -> None:
        """GeoDataFrameをキャッシュに保存。

        Args:
        ----
            data: 保存するGeoDataFrame
            cache_path: キャッシュファイルパス（BaseDataLoaderが生成）

        Raises:
        ------
            CacheError: 保存に失敗した場合

        """
        try:
            # GeoJSONとして保存
            data.to_file(cache_path, driver="GeoJSON")
            self.console.print(f"[green]キャッシュに保存: {cache_path}[/green]")
        except Exception as e:
            raise CacheError(f"キャッシュ保存に失敗しました: {e}") from e

    def _load_from_cache(self, cache_path: Path) -> gpd.GeoDataFrame:
        """キャッシュからGeoDataFrameを読み込み。

        Args:
        ----
            cache_path: キャッシュファイルパス（BaseDataLoaderが生成）

        Returns:
        -------
            キャッシュされたGeoDataFrame

        Raises:
        ------
            CacheError: 読み込みに失敗した場合

        """
        try:
            return gpd.read_file(cache_path)
        except Exception as e:
            raise CacheError(f"キャッシュ読み込みに失敗しました: {e}") from e
