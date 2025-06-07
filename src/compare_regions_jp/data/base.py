"""データローダー抽象基底クラス。

統一されたキャッシュ機能、エラーハンドリング、実行時間計測を提供する。
"""

import hashlib
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from compare_regions_jp.config.settings import get_settings


@dataclass
class DataLoadResult:
    """データロード結果を表すデータクラス。

    Attributes
    ----------
        data: ロードされたデータ
        source: データソース（ファイルパス、URL等）
        cached: キャッシュから取得されたかどうか
        load_time_seconds: ロード時間（秒）
        cache_path: キャッシュファイルのパス（存在する場合）
        metadata: 追加のメタデータ
    """

    data: Any
    source: str
    cached: bool
    load_time_seconds: float
    cache_path: Path | None = None
    metadata: dict[str, Any] | None = None


class DataLoadError(Exception):
    """データロード時のエラー。"""

    def __init__(
        self, message: str, source: str, original_error: Exception | None = None
    ):
        """エラーを初期化。

        Args:
        ----
            message: エラーメッセージ
            source: データソース
            original_error: 元の例外
        """
        super().__init__(message)
        self.source = source
        self.original_error = original_error


class CacheError(Exception):
    """キャッシュ操作時のエラー。"""

    pass


class BaseDataLoader(ABC):
    """データローダー抽象基底クラス。

    キャッシュ機能、エラーハンドリング、実行時間計測機能を提供する。
    具象クラスは_load_data_from_sourceメソッドを実装する必要がある。
    """

    def __init__(
        self,
        cache_enabled: bool = True,
        cache_ttl_hours: int | None = None,
        cache_dir: Path | None = None,
    ):
        """データローダーを初期化。

        Args:
        ----
            cache_enabled: キャッシュ機能の有効/無効
            cache_ttl_hours: キャッシュ有効期限（時間）。Noneの場合は設定値を使用
            cache_dir: キャッシュディレクトリ。Noneの場合は設定値を使用
        """
        settings = get_settings()
        self.cache_enabled = cache_enabled and settings.cache_enabled
        self.cache_ttl_hours = cache_ttl_hours or settings.cache_ttl_hours
        self.cache_dir = cache_dir or settings.cache_dir

        if self.cache_enabled:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    def load_data(self, source: str, **kwargs: Any) -> DataLoadResult:
        """データをロードする。

        キャッシュが有効で有効期限内のデータが存在する場合はキャッシュから取得。
        そうでなければソースから直接ロードし、キャッシュに保存する。

        Args:
        ----
            source: データソース（URL、ファイルパス等）
            **kwargs: ローダー固有の追加パラメータ

        Returns:
        -------
            データロード結果

        Raises:
        ------
            DataLoadError: データロードに失敗した場合
            CacheError: キャッシュ操作に失敗した場合
        """
        start_time = time.time()

        try:
            # キャッシュから取得を試行
            if self.cache_enabled:
                cache_path = self._get_cache_path(source, **kwargs)
                if self._is_cache_valid(cache_path):
                    try:
                        data = self._load_from_cache(cache_path)
                        load_time = time.time() - start_time
                        return DataLoadResult(
                            data=data,
                            source=source,
                            cached=True,
                            load_time_seconds=load_time,
                            cache_path=cache_path,
                            metadata={"cache_ttl_hours": self.cache_ttl_hours},
                        )
                    except Exception as e:
                        # キャッシュ読み込みに失敗した場合は警告してソースから取得
                        self._handle_cache_error(f"キャッシュ読み込み失敗: {e}", cache_path)

            # ソースから直接ロード
            data = self._load_data_from_source(source, **kwargs)
            load_time = time.time() - start_time

            # キャッシュに保存
            cache_path_save: Path | None = None
            if self.cache_enabled:
                try:
                    cache_path_save = self._get_cache_path(source, **kwargs)
                    self._save_to_cache(data, cache_path_save)
                except Exception as e:
                    # キャッシュ保存に失敗しても継続
                    self._handle_cache_error(f"キャッシュ保存失敗: {e}", cache_path_save)

            return DataLoadResult(
                data=data,
                source=source,
                cached=False,
                load_time_seconds=load_time,
                cache_path=cache_path_save,
                metadata={"cache_ttl_hours": self.cache_ttl_hours},
            )

        except DataLoadError:
            raise
        except Exception as e:
            raise DataLoadError(f"データロードに失敗しました: {e}", source, original_error=e) from e

    @abstractmethod
    def _load_data_from_source(self, source: str, **kwargs: Any) -> Any:
        """ソースからデータを直接ロードする（抽象メソッド）。

        Args:
        ----
            source: データソース
            **kwargs: ローダー固有の追加パラメータ

        Returns:
        -------
            ロードされたデータ

        Raises:
        ------
            DataLoadError: ロードに失敗した場合
        """
        pass

    @abstractmethod
    def _save_to_cache(self, data: Any, cache_path: Path) -> None:
        """データをキャッシュに保存する（抽象メソッド）。

        Args:
        ----
            data: 保存するデータ
            cache_path: キャッシュファイルパス

        Raises:
        ------
            CacheError: 保存に失敗した場合
        """
        pass

    @abstractmethod
    def _load_from_cache(self, cache_path: Path) -> Any:
        """キャッシュからデータを読み込む（抽象メソッド）。

        Args:
        ----
            cache_path: キャッシュファイルパス

        Returns:
        -------
            ロードされたデータ

        Raises:
        ------
            CacheError: 読み込みに失敗した場合
        """
        pass

    def _get_cache_path(self, source: str, **kwargs: Any) -> Path:
        """キャッシュファイルパスを生成する。

        ソースとパラメータのハッシュ値を使用してユニークなパスを生成。

        Args:
        ----
            source: データソース
            **kwargs: 追加パラメータ

        Returns:
        -------
            キャッシュファイルパス
        """
        # ソースとパラメータからハッシュ値を生成
        cache_key = f"{source}_{sorted(kwargs.items())}"
        hash_value = hashlib.sha256(cache_key.encode()).hexdigest()[:16]

        # ローダー名を含むファイル名を生成
        loader_name = self.__class__.__name__.lower().replace("loader", "")
        filename = f"{loader_name}_{hash_value}.cache"

        return self.cache_dir / filename

    def _is_cache_valid(self, cache_path: Path) -> bool:
        """キャッシュが有効かどうかを判定する。

        Args:
        ----
            cache_path: キャッシュファイルパス

        Returns:
        -------
            キャッシュが有効な場合True
        """
        if not cache_path.exists():
            return False

        # TTLチェック
        cache_age_hours = (time.time() - cache_path.stat().st_mtime) / 3600
        return cache_age_hours <= self.cache_ttl_hours

    def _handle_cache_error(self, message: str, cache_path: Path | None = None) -> None:
        """キャッシュエラーを処理する。

        Args:
        ----
            message: エラーメッセージ
            cache_path: 問題のあるキャッシュファイルパス
        """
        # デバッグ設定の場合はエラーを出力
        settings = get_settings()
        if settings.debug:
            from rich.console import Console

            console = Console()
            console.print(f"[yellow]警告: {message}[/yellow]")

        # 破損したキャッシュファイルを削除
        if cache_path and cache_path.exists():
            try:
                cache_path.unlink()
            except Exception:
                pass  # 削除に失敗しても継続

    def clear_cache(self, source: str | None = None, **kwargs: Any) -> int:
        """キャッシュをクリアする。

        Args:
        ----
            source: 特定のソースのキャッシュのみクリア。Noneの場合は全体をクリア
            **kwargs: ソースに関連する追加パラメータ

        Returns:
        -------
            削除されたファイル数
        """
        if not self.cache_enabled or not self.cache_dir.exists():
            return 0

        deleted_count = 0

        if source is None:
            # 全体をクリア
            loader_prefix = self.__class__.__name__.lower().replace("loader", "")
            for cache_file in self.cache_dir.glob(f"{loader_prefix}_*.cache"):
                try:
                    cache_file.unlink()
                    deleted_count += 1
                except Exception:
                    pass
        else:
            # 特定のソースのキャッシュをクリア
            cache_path = self._get_cache_path(source, **kwargs)
            if cache_path.exists():
                try:
                    cache_path.unlink()
                    deleted_count = 1
                except Exception:
                    pass

        return deleted_count

    def get_cache_info(self) -> dict[str, Any]:
        """キャッシュ情報を取得する。

        Returns
        -------
            キャッシュ情報の辞書
        """
        if not self.cache_enabled or not self.cache_dir.exists():
            return {
                "enabled": False,
                "cache_dir": str(self.cache_dir),
                "ttl_hours": self.cache_ttl_hours,
                "file_count": 0,
                "total_size_bytes": 0,
            }

        # ローダー固有のキャッシュファイルを検索
        loader_prefix = self.__class__.__name__.lower().replace("loader", "")
        cache_files = list(self.cache_dir.glob(f"{loader_prefix}_*.cache"))

        total_size = sum(f.stat().st_size for f in cache_files if f.exists())

        return {
            "enabled": True,
            "cache_dir": str(self.cache_dir),
            "ttl_hours": self.cache_ttl_hours,
            "file_count": len(cache_files),
            "total_size_bytes": total_size,
            "files": [
                {
                    "path": str(f),
                    "size_bytes": f.stat().st_size,
                    "modified_time": f.stat().st_mtime,
                    "age_hours": (time.time() - f.stat().st_mtime) / 3600,
                    "valid": self._is_cache_valid(f),
                }
                for f in cache_files
                if f.exists()
            ],
        }
