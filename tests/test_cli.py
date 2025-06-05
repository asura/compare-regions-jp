"""CLI テスト"""

from click.testing import CliRunner
from compare_regions_jp.cli import cli


def test_cli_help():
    """ヘルプが表示される"""
    runner = CliRunner()
    result = runner.invoke(cli, ['--help'])
    assert result.exit_code == 0
    assert 'compare' in result.output


def test_compare_command_basic():
    """基本的な比較コマンド"""
    runner = CliRunner()
    result = runner.invoke(cli, [
        'compare',
        '--addr-a', '東京都港区赤坂',
        '--addr-b', '東京都新宿区新宿'
    ])
    # 現状は実装中なのでエラーにならないことを確認
    assert result.exit_code == 0
