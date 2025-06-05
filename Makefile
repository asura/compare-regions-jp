.PHONY: setup install test lint format clean dev check help

help:
	@echo "compare-regions-jp 開発用Makefile"
	@echo ""
	@echo "利用可能なコマンド:"
	@echo "  setup     - 初回環境セットアップ"
	@echo "  install   - 依存関係インストール"
	@echo "  test      - テスト実行"
	@echo "  lint      - コード品質チェック"
	@echo "  format    - コードフォーマット"
	@echo "  check     - 全品質チェック（lint + test）"
	@echo "  clean     - キャッシュクリア"
	@echo "  dev       - 開発モード（format + lint + test）"

setup:
	@echo "🚀 初回環境セットアップを開始..."
	poetry install
	poetry run pre-commit install
	@echo "✅ セットアップ完了"

install:
	poetry install

test:
	@echo "🧪 テスト実行中..."
	poetry run pytest

lint:
	@echo "🔍 コード品質チェック中..."
	poetry run ruff check src/ tests/
	poetry run mypy src/

format:
	@echo "🎨 コードフォーマット中..."
	poetry run black src/ tests/
	poetry run ruff --fix src/ tests/

check: lint test
	@echo "✅ 全品質チェック完了"

dev: format lint test
	@echo "🎯 開発チェック完了"

clean:
	@echo "🧹 キャッシュクリア中..."
	find . -type d -name __pycache__ -delete
	find . -name "*.pyc" -delete
	rm -rf .pytest_cache .mypy_cache .coverage htmlcov/
	rm -rf dist/ build/ *.egg-info/

run-help:
	poetry run compare-regions-jp --help

update:
	poetry update
