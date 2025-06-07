"""設定管理モジュール。

Pydantic Settingsを使用して環境変数とデフォルト設定を管理する。
"""

import os
from pathlib import Path
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):  # type: ignore[misc]
    """アプリケーション設定クラス。

    環境変数から設定を読み取り、デフォルト値を提供する。
    設定値の検証機能も含む。
    """

    # API設定
    api_timeout: int = Field(
        default=30, description="API呼び出しのタイムアウト時間（秒）", ge=1, le=300
    )

    api_retry_count: int = Field(default=3, description="API呼び出しのリトライ回数", ge=0, le=10)

    api_base_url: str = Field(
        default="https://api.example.com", description="APIのベースURL"
    )

    api_key: str | None = Field(
        default=None, description="APIキー（環境変数COMPARE_REGIONS_API_KEYから取得）"
    )

    # キャッシュ設定
    cache_enabled: bool = Field(default=True, description="キャッシュ機能の有効/無効")

    cache_dir: Path = Field(
        default=Path.home() / ".cache" / "compare-regions-jp",
        description="キャッシュディレクトリのパス",
    )

    cache_ttl_hours: int = Field(
        default=24, description="キャッシュの有効期限（時間）", ge=1, le=168  # 1週間
    )

    cache_max_size_mb: int = Field(
        default=100, description="キャッシュの最大サイズ（MB）", ge=1, le=1000
    )

    # デバッグ設定
    debug: bool = Field(default=False, description="デバッグモードの有効/無効")

    log_level: str = Field(default="INFO", description="ログレベル")

    # データ取得設定
    data_sources: list[str] = Field(
        default=["opendata", "osm"], description="使用するデータソース"
    )

    max_concurrent_requests: int = Field(
        default=5, description="同時リクエスト数の上限", ge=1, le=20
    )

    # 出力設定
    output_format: str = Field(default="markdown", description="出力フォーマット")

    output_dir: Path = Field(default=Path.cwd() / "output", description="出力ディレクトリのパス")

    model_config = SettingsConfigDict(
        env_prefix="COMPARE_REGIONS_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """ログレベルの検証。

        Args:
        ----
            v: ログレベル文字列

        Returns:
        -------
            検証済みログレベル

        Raises:
        ------
            ValueError: 無効なログレベルの場合

        """
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in valid_levels:
            raise ValueError(f"ログレベルは {valid_levels} のいずれかである必要があります")
        return v.upper()

    @field_validator("output_format")
    @classmethod
    def validate_output_format(cls, v: str) -> str:
        """出力フォーマットの検証。

        Args:
        ----
            v: 出力フォーマット文字列

        Returns:
        -------
            検証済み出力フォーマット

        Raises:
        ------
            ValueError: 無効な出力フォーマットの場合

        """
        valid_formats = {"markdown", "json", "csv", "html"}
        if v.lower() not in valid_formats:
            raise ValueError(f"出力フォーマットは {valid_formats} のいずれかである必要があります")
        return v.lower()

    @field_validator("data_sources")
    @classmethod
    def validate_data_sources(cls, v: list[str]) -> list[str]:
        """データソースの検証。

        Args:
        ----
            v: データソースのリスト

        Returns:
        -------
            検証済みデータソースリスト

        Raises:
        ------
            ValueError: 無効なデータソースの場合

        """
        valid_sources = {"opendata", "osm", "resas", "estat"}
        invalid_sources = set(v) - valid_sources
        if invalid_sources:
            raise ValueError(
                f"無効なデータソース: {invalid_sources}. " f"有効なソース: {valid_sources}"
            )
        return v

    @field_validator("cache_dir", "output_dir")
    @classmethod
    def validate_directory_path(cls, v: Path) -> Path:
        """ディレクトリパスの検証。

        Args:
        ----
            v: ディレクトリパス

        Returns:
        -------
            検証済みディレクトリパス

        """
        # 親ディレクトリが存在しない場合は作成
        v.parent.mkdir(parents=True, exist_ok=True)
        return v

    def get_env_vars(self) -> dict[str, Any]:
        """環境変数の現在値を取得。

        Returns
        -------
            環境変数名と値の辞書

        """
        env_vars: dict[str, str] = {}
        env_prefix = "COMPARE_REGIONS_"
        for field_name in self.model_fields.keys():
            env_var_name = f"{env_prefix}{field_name.upper()}"
            env_value = os.getenv(env_var_name)
            if env_value is not None:
                env_vars[env_var_name] = env_value
        return env_vars

    def validate_configuration(self) -> dict[str, str]:
        """設定の妥当性をチェック。

        Returns
        -------
            検証結果の辞書（エラーがある場合のみ値を含む）

        """
        errors = {}

        # APIキーの確認
        if not self.api_key and "opendata" in self.data_sources:
            errors["api_key"] = "opendataを使用する場合はAPIキーが必要です"

        # キャッシュディレクトリの書き込み権限チェック
        if self.cache_enabled:
            try:
                self.cache_dir.mkdir(parents=True, exist_ok=True)
                test_file = self.cache_dir / ".test_write"
                test_file.touch()
                test_file.unlink()
            except (OSError, PermissionError):
                errors["cache_dir"] = f"キャッシュディレクトリに書き込み権限がありません: {self.cache_dir}"

        # 出力ディレクトリの書き込み権限チェック
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            test_file = self.output_dir / ".test_write"
            test_file.touch()
            test_file.unlink()
        except (OSError, PermissionError):
            errors["output_dir"] = f"出力ディレクトリに書き込み権限がありません: {self.output_dir}"

        return errors


# グローバル設定インスタンス
settings = AppSettings()


def get_settings() -> AppSettings:
    """設定インスタンスを取得。

    Returns
    -------
        アプリケーション設定インスタンス

    """
    return settings


def reload_settings() -> AppSettings:
    """設定を再読み込み。

    Returns
    -------
        新しい設定インスタンス

    """
    global settings
    settings = AppSettings()
    return settings
