"""設定管理のテスト。"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from compare_regions_jp.config.settings import (
    AppSettings,
    get_settings,
    reload_settings,
)
from pydantic import ValidationError


def describe_AppSettings():
    """AppSettingsクラスのテスト。"""

    def describe_デフォルト値():
        def APIタイムアウトのデフォルト値は30():
            settings = AppSettings()
            assert settings.api_timeout == 30

        def APIリトライ回数のデフォルト値は3():
            settings = AppSettings()
            assert settings.api_retry_count == 3

        def APIベースURLのデフォルト値が設定される():
            settings = AppSettings()
            assert settings.api_base_url == "https://api.example.com"

        def APIキーのデフォルト値はNone():
            settings = AppSettings()
            assert settings.api_key is None

        def キャッシュが有効になっている():
            settings = AppSettings()
            assert settings.cache_enabled is True

        def キャッシュディレクトリのデフォルト値が設定される():
            settings = AppSettings()
            expected_path = Path.home() / ".cache" / "compare-regions-jp"
            assert settings.cache_dir == expected_path

        def キャッシュTTLのデフォルト値は24時間():
            settings = AppSettings()
            assert settings.cache_ttl_hours == 24

        def キャッシュ最大サイズのデフォルト値は100MB():
            settings = AppSettings()
            assert settings.cache_max_size_mb == 100

        def デバッグモードのデフォルト値はFalse():
            settings = AppSettings()
            assert settings.debug is False

        def ログレベルのデフォルト値はINFO():
            settings = AppSettings()
            assert settings.log_level == "INFO"

        def データソースのデフォルト値が設定される():
            settings = AppSettings()
            assert settings.data_sources == ["opendata", "osm"]

        def 最大同時リクエスト数のデフォルト値は5():
            settings = AppSettings()
            assert settings.max_concurrent_requests == 5

        def 出力フォーマットのデフォルト値はmarkdown():
            settings = AppSettings()
            assert settings.output_format == "markdown"

        def 出力ディレクトリのデフォルト値が設定される():
            settings = AppSettings()
            expected_path = Path.cwd() / "output"
            assert settings.output_dir == expected_path

    def describe_環境変数読み込み():
        def APIタイムアウトを環境変数から読み込む():
            with patch.dict(os.environ, {"COMPARE_REGIONS_API_TIMEOUT": "60"}):
                settings = AppSettings()
                assert settings.api_timeout == 60

        def APIリトライ回数を環境変数から読み込む():
            with patch.dict(os.environ, {"COMPARE_REGIONS_API_RETRY_COUNT": "5"}):
                settings = AppSettings()
                assert settings.api_retry_count == 5

        def APIキーを環境変数から読み込む():
            with patch.dict(os.environ, {"COMPARE_REGIONS_API_KEY": "test-api-key"}):
                settings = AppSettings()
                assert settings.api_key == "test-api-key"

        def キャッシュ有効フラグを環境変数から読み込む():
            with patch.dict(os.environ, {"COMPARE_REGIONS_CACHE_ENABLED": "false"}):
                settings = AppSettings()
                assert settings.cache_enabled is False

        def デバッグフラグを環境変数から読み込む():
            with patch.dict(os.environ, {"COMPARE_REGIONS_DEBUG": "true"}):
                settings = AppSettings()
                assert settings.debug is True

        def ログレベルを環境変数から読み込む():
            with patch.dict(os.environ, {"COMPARE_REGIONS_LOG_LEVEL": "DEBUG"}):
                settings = AppSettings()
                assert settings.log_level == "DEBUG"

        def 出力フォーマットを環境変数から読み込む():
            with patch.dict(os.environ, {"COMPARE_REGIONS_OUTPUT_FORMAT": "json"}):
                settings = AppSettings()
                assert settings.output_format == "json"

        def 環境変数の大文字小文字を区別しない():
            with patch.dict(os.environ, {"compare_regions_debug": "true"}):
                settings = AppSettings()
                assert settings.debug is True

    def describe_フィールド検証():
        def APIタイムアウトの最小値1が有効():
            settings = AppSettings(api_timeout=1)
            assert settings.api_timeout == 1

        def APIタイムアウトの最大値300が有効():
            settings = AppSettings(api_timeout=300)
            assert settings.api_timeout == 300

        def APIタイムアウト0は無効():
            with pytest.raises(ValidationError):
                AppSettings(api_timeout=0)

        def APIタイムアウト301は無効():
            with pytest.raises(ValidationError):
                AppSettings(api_timeout=301)

        def APIリトライ回数の最小値0が有効():
            settings = AppSettings(api_retry_count=0)
            assert settings.api_retry_count == 0

        def APIリトライ回数の最大値10が有効():
            settings = AppSettings(api_retry_count=10)
            assert settings.api_retry_count == 10

        def APIリトライ回数負の値は無効():
            with pytest.raises(ValidationError):
                AppSettings(api_retry_count=-1)

        def キャッシュTTL最小値1が有効():
            settings = AppSettings(cache_ttl_hours=1)
            assert settings.cache_ttl_hours == 1

        def キャッシュTTL最大値168が有効():
            settings = AppSettings(cache_ttl_hours=168)
            assert settings.cache_ttl_hours == 168

        def キャッシュTTL0は無効():
            with pytest.raises(ValidationError):
                AppSettings(cache_ttl_hours=0)

        def キャッシュTTL169は無効():
            with pytest.raises(ValidationError):
                AppSettings(cache_ttl_hours=169)

        def 最大同時リクエスト数の最小値1が有効():
            settings = AppSettings(max_concurrent_requests=1)
            assert settings.max_concurrent_requests == 1

        def 最大同時リクエスト数の最大値20が有効():
            settings = AppSettings(max_concurrent_requests=20)
            assert settings.max_concurrent_requests == 20

    def describe_ログレベル検証():
        def DEBUGが有効():
            settings = AppSettings(log_level="DEBUG")
            assert settings.log_level == "DEBUG"

        def INFOが有効():
            settings = AppSettings(log_level="INFO")
            assert settings.log_level == "INFO"

        def WARNINGが有効():
            settings = AppSettings(log_level="WARNING")
            assert settings.log_level == "WARNING"

        def ERRORが有効():
            settings = AppSettings(log_level="ERROR")
            assert settings.log_level == "ERROR"

        def CRITICALが有効():
            settings = AppSettings(log_level="CRITICAL")
            assert settings.log_level == "CRITICAL"

        def 小文字のdebugが大文字に変換される():
            settings = AppSettings(log_level="debug")
            assert settings.log_level == "DEBUG"

        def 小文字のinfoが大文字に変換される():
            settings = AppSettings(log_level="info")
            assert settings.log_level == "INFO"

        def 無効なログレベルでエラーが発生する():
            with pytest.raises(ValidationError) as exc_info:
                AppSettings(log_level="INVALID")
            assert "ログレベルは" in str(exc_info.value)

    def describe_出力フォーマット検証():
        def markdownが有効():
            settings = AppSettings(output_format="markdown")
            assert settings.output_format == "markdown"

        def jsonが有効():
            settings = AppSettings(output_format="json")
            assert settings.output_format == "json"

        def csvが有効():
            settings = AppSettings(output_format="csv")
            assert settings.output_format == "csv"

        def htmlが有効():
            settings = AppSettings(output_format="html")
            assert settings.output_format == "html"

        def 大文字のMARKDOWNが小文字に変換される():
            settings = AppSettings(output_format="MARKDOWN")
            assert settings.output_format == "markdown"

        def 大文字のJSONが小文字に変換される():
            settings = AppSettings(output_format="JSON")
            assert settings.output_format == "json"

        def 無効な出力フォーマットでエラーが発生する():
            with pytest.raises(ValidationError) as exc_info:
                AppSettings(output_format="invalid")
            assert "出力フォーマットは" in str(exc_info.value)

    def describe_データソース検証():
        def opendataのみが有効():
            settings = AppSettings(data_sources=["opendata"])
            assert settings.data_sources == ["opendata"]

        def 複数の有効なデータソースが使用できる():
            settings = AppSettings(data_sources=["opendata", "osm", "resas", "estat"])
            expected = ["opendata", "osm", "resas", "estat"]
            assert settings.data_sources == expected

        def 無効なデータソースでエラーが発生する():
            with pytest.raises(ValidationError) as exc_info:
                AppSettings(data_sources=["invalid_source"])
            assert "無効なデータソース" in str(exc_info.value)

    def describe_メソッド():
        def get_env_varsがAPIキーを取得する():
            env_vars = {"COMPARE_REGIONS_API_KEY": "test-key"}
            with patch.dict(os.environ, env_vars):
                settings = AppSettings()
                env_result = settings.get_env_vars()
                assert env_result["COMPARE_REGIONS_API_KEY"] == "test-key"

        def get_env_varsがデバッグフラグを取得する():
            env_vars = {"COMPARE_REGIONS_DEBUG": "true"}
            with patch.dict(os.environ, env_vars):
                settings = AppSettings()
                env_result = settings.get_env_vars()
                assert env_result["COMPARE_REGIONS_DEBUG"] == "true"

    def describe_設定検証():
        def 有効な設定で検証が成功する():
            with tempfile.TemporaryDirectory() as temp_dir:
                cache_dir = Path(temp_dir) / "cache"
                output_dir = Path(temp_dir) / "output"

                settings = AppSettings(
                    api_key="test-key",
                    cache_dir=cache_dir,
                    output_dir=output_dir,
                    data_sources=["opendata"],
                )

                errors = settings.validate_configuration()
                assert errors == {}

        def APIキーなしでopendataを使用するとエラーが発生する():
            settings = AppSettings(api_key=None, data_sources=["opendata"])

            errors = settings.validate_configuration()
            assert "api_key" in errors

        def APIキーエラーメッセージが適切():
            settings = AppSettings(api_key=None, data_sources=["opendata"])

            errors = settings.validate_configuration()
            assert "APIキーが必要" in errors["api_key"]

        def OSMのみの場合はAPIキーエラーなし():
            settings = AppSettings(data_sources=["osm"])

            errors = settings.validate_configuration()
            assert "api_key" not in errors

    def describe_ディレクトリ処理():
        def キャッシュディレクトリの親が自動作成される():
            with tempfile.TemporaryDirectory() as temp_dir:
                cache_dir = Path(temp_dir) / "new_cache"

                AppSettings(cache_dir=cache_dir)

                assert cache_dir.parent.exists()

        def 出力ディレクトリの親が自動作成される():
            with tempfile.TemporaryDirectory() as temp_dir:
                output_dir = Path(temp_dir) / "new_output"

                AppSettings(output_dir=output_dir)

                assert output_dir.parent.exists()


def describe_グローバル関数():
    def get_settingsがAppSettingsインスタンスを返す():
        settings = get_settings()
        assert isinstance(settings, AppSettings)

    def reload_settingsがAppSettingsインスタンスを返す():
        new_settings = reload_settings()
        assert isinstance(new_settings, AppSettings)

    def reload_settingsが環境変数を再読み込みする():
        with patch.dict(os.environ, {"COMPARE_REGIONS_DEBUG": "true"}):
            new_settings = reload_settings()
            assert new_settings.debug is True

    def reload_settingsがグローバル設定を更新する():
        with patch.dict(os.environ, {"COMPARE_REGIONS_DEBUG": "true"}):
            reload_settings()
            assert get_settings().debug is True


def describe_設定シナリオ():
    def describe_本番環境設定():
        def APIキーが設定される():
            env_vars = {"COMPARE_REGIONS_API_KEY": "prod-api-key"}
            with patch.dict(os.environ, env_vars):
                settings = AppSettings()
                assert settings.api_key == "prod-api-key"

        def デバッグが無効になる():
            env_vars = {"COMPARE_REGIONS_DEBUG": "false"}
            with patch.dict(os.environ, env_vars):
                settings = AppSettings()
                assert settings.debug is False

        def ログレベルがWARNINGになる():
            env_vars = {"COMPARE_REGIONS_LOG_LEVEL": "WARNING"}
            with patch.dict(os.environ, env_vars):
                settings = AppSettings()
                assert settings.log_level == "WARNING"

        def キャッシュが有効になる():
            env_vars = {"COMPARE_REGIONS_CACHE_ENABLED": "true"}
            with patch.dict(os.environ, env_vars):
                settings = AppSettings()
                assert settings.cache_enabled is True

        def キャッシュTTLが72時間になる():
            env_vars = {"COMPARE_REGIONS_CACHE_TTL_HOURS": "72"}
            with patch.dict(os.environ, env_vars):
                settings = AppSettings()
                assert settings.cache_ttl_hours == 72

        def 最大同時リクエスト数が10になる():
            env_vars = {"COMPARE_REGIONS_MAX_CONCURRENT_REQUESTS": "10"}
            with patch.dict(os.environ, env_vars):
                settings = AppSettings()
                assert settings.max_concurrent_requests == 10

    def describe_開発環境設定():
        def デバッグが有効になる():
            env_vars = {"COMPARE_REGIONS_DEBUG": "true"}
            with patch.dict(os.environ, env_vars):
                settings = AppSettings()
                assert settings.debug is True

        def ログレベルがDEBUGになる():
            env_vars = {"COMPARE_REGIONS_LOG_LEVEL": "DEBUG"}
            with patch.dict(os.environ, env_vars):
                settings = AppSettings()
                assert settings.log_level == "DEBUG"

        def キャッシュが無効になる():
            env_vars = {"COMPARE_REGIONS_CACHE_ENABLED": "false"}
            with patch.dict(os.environ, env_vars):
                settings = AppSettings()
                assert settings.cache_enabled is False

        def 出力フォーマットがjsonになる():
            env_vars = {"COMPARE_REGIONS_OUTPUT_FORMAT": "json"}
            with patch.dict(os.environ, env_vars):
                settings = AppSettings()
                assert settings.output_format == "json"
