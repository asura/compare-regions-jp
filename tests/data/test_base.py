"""データローダー抽象基底クラスのテスト。"""

import json
import tempfile
import time
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

import pytest
from compare_regions_jp.data.base import (
    BaseDataLoader,
    CacheError,
    DataLoadError,
    DataLoadResult,
)


class TestDataLoader(BaseDataLoader):
    """テスト用のデータローダー実装。"""

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self.load_call_count = 0
        self.save_call_count = 0
        self.test_data = {"test": "data", "timestamp": time.time()}

    def _load_data_from_source(self, source: str, **kwargs: Any) -> dict[str, Any]:
        self.load_call_count += 1
        if source == "error_source":
            raise DataLoadError("テストエラー", source)
        return {**self.test_data, "source": source, **kwargs}

    def _save_to_cache(self, data: Any, cache_path: Path) -> None:
        self.save_call_count += 1
        if cache_path.name.startswith("error_"):
            raise CacheError("キャッシュ保存エラー")
        with open(cache_path, "w") as f:
            json.dump(data, f)

    def _load_from_cache(self, cache_path: Path) -> dict[str, Any]:
        if cache_path.name.startswith("error_"):
            raise CacheError("キャッシュ読み込みエラー")
        with open(cache_path) as f:
            return json.load(f)


def describe_DataLoadResult():
    """DataLoadResultの動作テスト。"""

    def データクラスが正しく初期化される():
        result = DataLoadResult(
            data={"test": "data"},
            source="test_source",
            cached=True,
            load_time_seconds=1.5,
            cache_path=Path("/tmp/cache"),
            metadata={"key": "value"},
        )

        assert result.data == {"test": "data"}
        assert result.source == "test_source"
        assert result.cached is True
        assert result.load_time_seconds == 1.5
        assert result.cache_path == Path("/tmp/cache")
        assert result.metadata == {"key": "value"}

    def オプショナル引数がデフォルト値になる():
        result = DataLoadResult(
            data={"test": "data"},
            source="test_source",
            cached=False,
            load_time_seconds=1.0,
        )

        assert result.cache_path is None
        assert result.metadata is None


def describe_DataLoadError():
    """DataLoadErrorの動作テスト。"""

    def エラーメッセージとソースが設定される():
        error = DataLoadError("テストエラー", "test_source")

        assert str(error) == "テストエラー"
        assert error.source == "test_source"
        assert error.original_error is None

    def 元の例外が保持される():
        original = ValueError("元のエラー")
        error = DataLoadError("ラップされたエラー", "test_source", original)

        assert error.original_error is original


def describe_CacheError():
    """CacheErrorの動作テスト。"""

    def 基本的な例外として動作する():
        error = CacheError("キャッシュエラー")
        assert str(error) == "キャッシュエラー"


def describe_BaseDataLoader():
    """BaseDataLoaderの動作テスト。"""

    def describe_初期化():
        def デフォルト設定で初期化される():
            with tempfile.TemporaryDirectory() as temp_dir:
                with patch(
                    "compare_regions_jp.data.base.get_settings"
                ) as mock_settings:
                    mock_settings.return_value = Mock(
                        cache_enabled=True,
                        cache_ttl_hours=24,
                        cache_dir=Path(temp_dir),
                    )

                    loader = TestDataLoader()

                    assert loader.cache_enabled is True
                    assert loader.cache_ttl_hours == 24
                    assert loader.cache_dir == Path(temp_dir)

        def カスタム設定で初期化される():
            with tempfile.TemporaryDirectory() as temp_dir:
                custom_cache_dir = Path(temp_dir) / "custom"

                with patch(
                    "compare_regions_jp.data.base.get_settings"
                ) as mock_settings:
                    mock_settings.return_value = Mock(
                        cache_enabled=True,
                        cache_ttl_hours=12,
                        cache_dir=Path(temp_dir),
                    )

                    loader = TestDataLoader(
                        cache_enabled=False,
                        cache_ttl_hours=48,
                        cache_dir=custom_cache_dir,
                    )

                    assert loader.cache_enabled is False
                    assert loader.cache_ttl_hours == 48
                    assert loader.cache_dir == custom_cache_dir

        def キャッシュディレクトリが自動作成される():
            with tempfile.TemporaryDirectory() as temp_dir:
                cache_dir = Path(temp_dir) / "new_cache"

                with patch(
                    "compare_regions_jp.data.base.get_settings"
                ) as mock_settings:
                    mock_settings.return_value = Mock(
                        cache_enabled=True,
                        cache_ttl_hours=24,
                        cache_dir=cache_dir,
                    )

                    TestDataLoader()

                    assert cache_dir.exists()

    def describe_データロード():
        def ソースから正常にロードされる():
            with tempfile.TemporaryDirectory() as temp_dir:
                with patch(
                    "compare_regions_jp.data.base.get_settings"
                ) as mock_settings:
                    mock_settings.return_value = Mock(
                        cache_enabled=True,
                        cache_ttl_hours=24,
                        cache_dir=Path(temp_dir),
                    )

                    loader = TestDataLoader()
                    result = loader.load_data("test_source", param="value")

                    assert isinstance(result, DataLoadResult)
                    assert result.source == "test_source"
                    assert result.cached is False
                    assert result.load_time_seconds > 0
                    assert "test" in result.data

        def 実行時間が正確に計測される():
            with tempfile.TemporaryDirectory() as temp_dir:
                with patch(
                    "compare_regions_jp.data.base.get_settings"
                ) as mock_settings:
                    mock_settings.return_value = Mock(
                        cache_enabled=False,
                        cache_ttl_hours=24,
                        cache_dir=Path(temp_dir),
                    )

                    loader = TestDataLoader()

                    with patch.object(loader, "_load_data_from_source") as mock_load:

                        def slow_load(*args, **kwargs):
                            time.sleep(0.1)
                            return {"test": "data"}

                        mock_load.side_effect = slow_load
                        result = loader.load_data("test_source")

                        assert result.load_time_seconds >= 0.1

        def データロードエラーが適切に処理される():
            with tempfile.TemporaryDirectory() as temp_dir:
                with patch(
                    "compare_regions_jp.data.base.get_settings"
                ) as mock_settings:
                    mock_settings.return_value = Mock(
                        cache_enabled=False,
                        cache_ttl_hours=24,
                        cache_dir=Path(temp_dir),
                    )

                    loader = TestDataLoader()

                    with pytest.raises(DataLoadError) as exc_info:
                        loader.load_data("error_source")

                    assert exc_info.value.source == "error_source"

        def 予期しない例外がDataLoadErrorでラップされる():
            with tempfile.TemporaryDirectory() as temp_dir:
                with patch(
                    "compare_regions_jp.data.base.get_settings"
                ) as mock_settings:
                    mock_settings.return_value = Mock(
                        cache_enabled=False,
                        cache_ttl_hours=24,
                        cache_dir=Path(temp_dir),
                    )

                    loader = TestDataLoader()

                    with patch.object(loader, "_load_data_from_source") as mock_load:
                        mock_load.side_effect = ValueError("予期しないエラー")

                        with pytest.raises(DataLoadError) as exc_info:
                            loader.load_data("test_source")

                        assert "データロードに失敗しました" in str(exc_info.value)
                        assert isinstance(exc_info.value.original_error, ValueError)

    def describe_キャッシュ機能():
        def キャッシュが無効な場合は常にソースからロード():
            with tempfile.TemporaryDirectory() as temp_dir:
                with patch(
                    "compare_regions_jp.data.base.get_settings"
                ) as mock_settings:
                    mock_settings.return_value = Mock(
                        cache_enabled=False,
                        cache_ttl_hours=24,
                        cache_dir=Path(temp_dir),
                    )

                    loader = TestDataLoader(cache_enabled=False)

                    # 最初のロード
                    result1 = loader.load_data("test_source")
                    assert result1.cached is False

                    # 2回目のロード
                    result2 = loader.load_data("test_source")
                    assert result2.cached is False

                    # ソースから2回ロードされている
                    assert loader.load_call_count == 2

        def キャッシュからデータがロードされる():
            with tempfile.TemporaryDirectory() as temp_dir:
                with patch(
                    "compare_regions_jp.data.base.get_settings"
                ) as mock_settings:
                    mock_settings.return_value = Mock(
                        cache_enabled=True,
                        cache_ttl_hours=24,
                        cache_dir=Path(temp_dir),
                    )

                    loader = TestDataLoader()

                    # 最初のロード（キャッシュに保存）
                    result1 = loader.load_data("test_source")
                    assert result1.cached is False
                    assert loader.load_call_count == 1

                    # 2回目のロード（キャッシュから取得）
                    result2 = loader.load_data("test_source")
                    assert result2.cached is True
                    assert loader.load_call_count == 1  # ソースからは1回のみ

        def 期限切れキャッシュは無視される():
            with tempfile.TemporaryDirectory() as temp_dir:
                with patch(
                    "compare_regions_jp.data.base.get_settings"
                ) as mock_settings:
                    mock_settings.return_value = Mock(
                        cache_enabled=True,
                        cache_ttl_hours=0.000001,  # より短時間
                        cache_dir=Path(temp_dir),
                    )

                    loader = TestDataLoader(cache_ttl_hours=0.000001)

                    # 最初のロード
                    loader.load_data("test_source")

                    # 十分に待つ
                    time.sleep(0.1)

                    # 2回目のロード（期限切れなのでソースから）
                    result2 = loader.load_data("test_source")
                    assert result2.cached is False
                    assert loader.load_call_count == 2

        def キャッシュ読み込みエラーでソースからロード():
            with tempfile.TemporaryDirectory() as temp_dir:
                with patch(
                    "compare_regions_jp.data.base.get_settings"
                ) as mock_settings:
                    mock_settings.return_value = Mock(
                        cache_enabled=True,
                        cache_ttl_hours=24,
                        cache_dir=Path(temp_dir),
                        debug=False,
                    )

                    loader = TestDataLoader()

                    # エラーを起こすキャッシュパスを作成
                    cache_path = loader._get_cache_path("error_cache_source")
                    cache_path.write_text("invalid json")

                    # ロード（キャッシュエラーでソースから取得）
                    result = loader.load_data("error_cache_source")
                    assert result.cached is False

        def キャッシュ保存エラーでも処理が継続される():
            with tempfile.TemporaryDirectory() as temp_dir:
                with patch(
                    "compare_regions_jp.data.base.get_settings"
                ) as mock_settings:
                    mock_settings.return_value = Mock(
                        cache_enabled=True,
                        cache_ttl_hours=24,
                        cache_dir=Path(temp_dir),
                        debug=False,
                    )

                    loader = TestDataLoader()

                    # キャッシュ保存でエラーが発生するソース
                    result = loader.load_data("error_save_source")

                    # エラーに関わらず結果は返される
                    assert result.cached is False
                    assert result.data is not None

    def describe_キャッシュパス生成():
        def ソースとパラメータからユニークなパスが生成される():
            with tempfile.TemporaryDirectory() as temp_dir:
                with patch(
                    "compare_regions_jp.data.base.get_settings"
                ) as mock_settings:
                    mock_settings.return_value = Mock(
                        cache_enabled=True,
                        cache_ttl_hours=24,
                        cache_dir=Path(temp_dir),
                    )

                    loader = TestDataLoader()

                    path1 = loader._get_cache_path("source1", param="a")
                    path2 = loader._get_cache_path("source2", param="a")
                    path3 = loader._get_cache_path("source1", param="b")

                    # 全て異なるパス
                    assert path1 != path2
                    assert path1 != path3
                    assert path2 != path3

        def 同じソースとパラメータで同じパスが生成される():
            with tempfile.TemporaryDirectory() as temp_dir:
                with patch(
                    "compare_regions_jp.data.base.get_settings"
                ) as mock_settings:
                    mock_settings.return_value = Mock(
                        cache_enabled=True,
                        cache_ttl_hours=24,
                        cache_dir=Path(temp_dir),
                    )

                    loader = TestDataLoader()

                    path1 = loader._get_cache_path("source", param="value")
                    path2 = loader._get_cache_path("source", param="value")

                    assert path1 == path2

        def ローダー名がファイル名に含まれる():
            with tempfile.TemporaryDirectory() as temp_dir:
                with patch(
                    "compare_regions_jp.data.base.get_settings"
                ) as mock_settings:
                    mock_settings.return_value = Mock(
                        cache_enabled=True,
                        cache_ttl_hours=24,
                        cache_dir=Path(temp_dir),
                    )

                    loader = TestDataLoader()
                    path = loader._get_cache_path("source")

                    assert "testdata_" in path.name
                    assert path.name.endswith(".cache")

    def describe_キャッシュ有効性判定():
        def 存在しないファイルは無効():
            with tempfile.TemporaryDirectory() as temp_dir:
                with patch(
                    "compare_regions_jp.data.base.get_settings"
                ) as mock_settings:
                    mock_settings.return_value = Mock(
                        cache_enabled=True,
                        cache_ttl_hours=24,
                        cache_dir=Path(temp_dir),
                    )

                    loader = TestDataLoader()
                    cache_path = Path(temp_dir) / "nonexistent.cache"

                    assert loader._is_cache_valid(cache_path) is False

        def 期限内のファイルは有効():
            with tempfile.TemporaryDirectory() as temp_dir:
                with patch(
                    "compare_regions_jp.data.base.get_settings"
                ) as mock_settings:
                    mock_settings.return_value = Mock(
                        cache_enabled=True,
                        cache_ttl_hours=24,
                        cache_dir=Path(temp_dir),
                    )

                    loader = TestDataLoader()
                    cache_path = Path(temp_dir) / "valid.cache"
                    cache_path.write_text("test")

                    assert loader._is_cache_valid(cache_path) is True

        def 期限切れファイルは無効():
            with tempfile.TemporaryDirectory() as temp_dir:
                with patch(
                    "compare_regions_jp.data.base.get_settings"
                ) as mock_settings:
                    mock_settings.return_value = Mock(
                        cache_enabled=True,
                        cache_ttl_hours=1,
                        cache_dir=Path(temp_dir),
                    )

                    loader = TestDataLoader(cache_ttl_hours=0.000001)
                    cache_path = Path(temp_dir) / "expired.cache"
                    cache_path.write_text("test")

                    # 十分に待って期限切れにする
                    time.sleep(0.1)

                    assert loader._is_cache_valid(cache_path) is False

    def describe_キャッシュクリア():
        def 全体クリアが正常に動作する():
            with tempfile.TemporaryDirectory() as temp_dir:
                with patch(
                    "compare_regions_jp.data.base.get_settings"
                ) as mock_settings:
                    mock_settings.return_value = Mock(
                        cache_enabled=True,
                        cache_ttl_hours=24,
                        cache_dir=Path(temp_dir),
                    )

                    loader = TestDataLoader()

                    # 複数のキャッシュを作成
                    loader.load_data("source1")
                    loader.load_data("source2")

                    # クリア実行
                    deleted_count = loader.clear_cache()

                    assert deleted_count == 2

        def 特定ソースのクリアが正常に動作する():
            with tempfile.TemporaryDirectory() as temp_dir:
                with patch(
                    "compare_regions_jp.data.base.get_settings"
                ) as mock_settings:
                    mock_settings.return_value = Mock(
                        cache_enabled=True,
                        cache_ttl_hours=24,
                        cache_dir=Path(temp_dir),
                    )

                    loader = TestDataLoader()

                    # 複数のキャッシュを作成
                    loader.load_data("source1")
                    loader.load_data("source2")

                    # 特定ソースをクリア
                    deleted_count = loader.clear_cache("source1")

                    assert deleted_count == 1

                    # source2のキャッシュは残っている
                    result = loader.load_data("source2")
                    assert result.cached is True

        def キャッシュ無効時はゼロが返される():
            with tempfile.TemporaryDirectory() as temp_dir:
                with patch(
                    "compare_regions_jp.data.base.get_settings"
                ) as mock_settings:
                    mock_settings.return_value = Mock(
                        cache_enabled=False,
                        cache_ttl_hours=24,
                        cache_dir=Path(temp_dir),
                    )

                    loader = TestDataLoader(cache_enabled=False)
                    deleted_count = loader.clear_cache()

                    assert deleted_count == 0

    def describe_キャッシュ情報取得():
        def キャッシュ無効時の情報が正しく返される():
            with tempfile.TemporaryDirectory() as temp_dir:
                with patch(
                    "compare_regions_jp.data.base.get_settings"
                ) as mock_settings:
                    mock_settings.return_value = Mock(
                        cache_enabled=False,
                        cache_ttl_hours=24,
                        cache_dir=Path(temp_dir),
                    )

                    loader = TestDataLoader(cache_enabled=False)
                    info = loader.get_cache_info()

                    assert info["enabled"] is False
                    assert info["file_count"] == 0
                    assert info["total_size_bytes"] == 0

        def キャッシュ有効時の詳細情報が返される():
            with tempfile.TemporaryDirectory() as temp_dir:
                with patch(
                    "compare_regions_jp.data.base.get_settings"
                ) as mock_settings:
                    mock_settings.return_value = Mock(
                        cache_enabled=True,
                        cache_ttl_hours=24,
                        cache_dir=Path(temp_dir),
                    )

                    loader = TestDataLoader()

                    # キャッシュファイルを作成
                    loader.load_data("source1")
                    loader.load_data("source2")

                    info = loader.get_cache_info()

                    assert info["enabled"] is True
                    assert info["file_count"] == 2
                    assert info["total_size_bytes"] > 0
                    assert len(info["files"]) == 2

                    # ファイル情報の確認
                    file_info = info["files"][0]
                    assert "path" in file_info
                    assert "size_bytes" in file_info
                    assert "modified_time" in file_info
                    assert "age_hours" in file_info
                    assert "valid" in file_info

    def describe_エラーハンドリング():
        def デバッグモード時にキャッシュエラーが表示される():
            with tempfile.TemporaryDirectory() as temp_dir:
                with patch(
                    "compare_regions_jp.data.base.get_settings"
                ) as mock_settings:
                    mock_settings.return_value = Mock(
                        cache_enabled=True,
                        cache_ttl_hours=24,
                        cache_dir=Path(temp_dir),
                        debug=True,
                    )

                    loader = TestDataLoader()

                    # rich.console.Consoleクラスをモック
                    with patch("rich.console.Console") as mock_console_class:
                        mock_console = Mock()
                        mock_console_class.return_value = mock_console

                        loader._handle_cache_error("テストエラー")

                        mock_console.print.assert_called_once()

        def 破損キャッシュファイルが削除される():
            with tempfile.TemporaryDirectory() as temp_dir:
                with patch(
                    "compare_regions_jp.data.base.get_settings"
                ) as mock_settings:
                    mock_settings.return_value = Mock(
                        cache_enabled=True,
                        cache_ttl_hours=24,
                        cache_dir=Path(temp_dir),
                        debug=False,
                    )

                    loader = TestDataLoader()

                    # 破損したキャッシュファイルを作成
                    cache_path = Path(temp_dir) / "corrupted.cache"
                    cache_path.write_text("corrupted data")

                    assert cache_path.exists()

                    loader._handle_cache_error("エラー", cache_path)

                    assert not cache_path.exists()
