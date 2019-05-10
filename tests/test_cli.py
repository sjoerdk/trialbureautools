from pathlib import Path
from unittest.mock import Mock

import pytest
from click.testing import CliRunner

from trialbureautools.cli.dicomsort import DicomSortCLI
from trialbureautools.cli.main import TrialBureauToolsCLI
from tests import RESOURCE_PATH


@pytest.fixture()
def mock_click_echo(monkeypatch):
    """Stop click from writing to console, capture to mock instead"""
    mock_echo = Mock()
    monkeypatch.setattr("trialbureautools.cli.dicomsort.click.echo", mock_echo)
    return mock_echo


@pytest.fixture()
def test_cli():
    return TrialBureauToolsCLI(config_path=RESOURCE_PATH / "tbt_test_config")


def test_cli_main(test_cli):
    runner = CliRunner()
    result = runner.invoke(test_cli.main)
    assert result.exit_code == 0


def test_cli_main(test_cli):
    runner = CliRunner()
    result = runner.invoke(test_cli.main, ["permissions"])
    assert result.exit_code == 0

    result = runner.invoke(test_cli.main, ["sort"])
    assert result.exit_code == 0


def test_cli_dicomsort_create_default_config(tmp_path, mock_click_echo):
    """When loaded with a non-existent config file path, dicomsort CLI should create a default one
    """

    config_file = Path(tmp_path) / "test_cli_config_file.yaml"
    assert not config_file.exists()
    DicomSortCLI(configuration_file=config_file)

    # file should have been created. And contain the default keys
    assert config_file.exists()
    loaded_patterns = DicomSortCLI(configuration_file=config_file).pattern_list
    assert list(loaded_patterns.keys()) == ["idis", "nucmed"]


def test_cli_dicomsort_add_key(tmp_path, mock_click_echo):
    """When loaded with a non-existent config file path, dicomsort CLI should create a default one
    """

    config_file = Path(tmp_path) / "test_add_cli_config_file.yaml"
    assert not config_file.exists()
    cli = DicomSortCLI(configuration_file=config_file)

    runner = CliRunner()
    runner.invoke(
        cli.get_click_commands()["add_pattern"], ["test", "/(PatientID)/somepath/"]
    )

    loaded_patterns = DicomSortCLI(configuration_file=config_file).pattern_list
    assert list(loaded_patterns.keys()) == ["idis", "nucmed", "test"]


def test_cli_dicomsort_remove_key(tmp_path, mock_click_echo):
    """When loaded with a non-existent config file path, dicomsort CLI should create a default one
    """

    config_file = Path(tmp_path) / "test_remove_cli_config_file.yaml"
    cli = DicomSortCLI(configuration_file=config_file)

    runner = CliRunner()
    runner.invoke(cli.get_click_commands()["remove_pattern"], ["idis"])

    loaded_patterns = DicomSortCLI(configuration_file=config_file).pattern_list
    assert list(loaded_patterns.keys()) == ["nucmed"]


def test_cli_dicomsort_list(tmp_path, mock_click_echo):
    """When loaded with a non-existent config file path, dicomsort CLI should create a default one
    """
    cli = DicomSortCLI(
        configuration_file=Path(tmp_path) / "test_remove_cli_config_file.yaml"
    )

    runner = CliRunner()
    result = runner.invoke(cli.get_click_commands()["list"])

    assert result.exit_code == 0
