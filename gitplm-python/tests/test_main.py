import pytest
from click.testing import CliRunner
from gitplm.main import cli

def test_version():
    """测试版本命令"""
    runner = CliRunner()
    result = runner.invoke(cli, ['--version'])
    assert result.exit_code == 0
    assert '0.1.0' in result.output

def test_release_command():
    """测试发布命令"""
    runner = CliRunner()
    result = runner.invoke(cli, ['release', 'PCB-056-0005'])
    assert result.exit_code == 0 