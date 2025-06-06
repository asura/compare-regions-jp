"""地域定義と境界取得"""

from abc import ABC, abstractmethod
from dataclasses import dataclass

import geopandas as gpd


@dataclass
class RegionSpec:
    """地域指定仕様"""

    region_type: str  # "address" or "station"
    primary: str  # 住所 or 駅名
    secondary: str | None = None  # 徒歩時間等


class Region(ABC):
    """地域抽象基底クラス"""

    def __init__(self, spec: RegionSpec):
        """初期化"""
        self.spec = spec
        self._geometry: gpd.GeoDataFrame | None = None

    @abstractmethod
    def get_geometry(self) -> gpd.GeoDataFrame:
        """地域の境界形状を取得"""
        pass

    @property
    def geometry(self) -> gpd.GeoDataFrame:
        """キャッシュされた境界形状"""
        if self._geometry is None:
            self._geometry = self.get_geometry()
        return self._geometry


class AddressRegion(Region):
    """住所ベース地域"""

    def get_geometry(self) -> gpd.GeoDataFrame:
        """住所から境界形状を取得"""
        # TODO: Nominatimでジオコーディング
        raise NotImplementedError("住所ジオコーディングは未実装")


class StationWalkRegion(Region):
    """駅徒歩圏地域"""

    def __init__(self, spec: RegionSpec, walk_minutes: int = 10):
        """初期化"""
        super().__init__(spec)
        self.walk_minutes = walk_minutes

    def get_geometry(self) -> gpd.GeoDataFrame:
        """駅徒歩圏の境界形状を取得"""
        # TODO: OSMnxで等時圏生成
        raise NotImplementedError("駅徒歩圏計算は未実装")


def create_region(spec: RegionSpec, **kwargs: int) -> Region:
    """地域仕様からRegionインスタンスを生成"""
    if spec.region_type == "address":
        return AddressRegion(spec)
    elif spec.region_type == "station":
        walk_minutes = kwargs.get("walk_minutes", 10)
        return StationWalkRegion(spec, walk_minutes)
    else:
        raise ValueError(f"未対応の地域タイプ: {spec.region_type}")
