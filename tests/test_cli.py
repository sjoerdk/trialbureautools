from pathlib import Path
from unittest.mock import Mock

import pytest
from click.testing import CliRunner

from trialbureautools.cli.dicomsort import DicomSortCLI
from trialbureautools.cli.main import TrialBureauToolsCLI
from tests import RESOURCE_PATH


@pytest.fixture()
def mock_click_echo(monkeypatch):
    """Stop click from writing to console, capture to string instead"""
    output = []
    mock_echo = lambda x: output.append(x)
    monkeypatch.setattr("trialbureautools.cli.dicomsort.click.echo", mock_echo)
    return output


@pytest.fixture()
def a_test_cli():
    """ A CLI that reads its tests from a pre-defined test config
    """
    return TrialBureauToolsCLI(config_path=RESOURCE_PATH / "tbt_test_config")


@pytest.fixture()
def a_default_cli(tmpdir, mock_click_echo):
    """A CLI that has a non-existent file as config. CLI will fill it with default contents"""
    config_file = Path(tmpdir) / "test_remove_cli_config_file.yaml"
    return DicomSortCLI(configuration_file=config_file)


@pytest.fixture()
def folderprocessing_mock_copyfile(monkeypatch):
    """Turn off copyfile, return mock that will records calls"""
    mock_copyfile = Mock()
    mock_makedirs = Mock()
    monkeypatch.setattr("dicomsort.folderprocessing.copyfile", mock_copyfile)
    monkeypatch.setattr("dicomsort.folderprocessing.makedirs", mock_makedirs)
    return mock_copyfile


def test_cli_main(a_test_cli):
    runner = CliRunner()
    result = runner.invoke(a_test_cli.main)
    assert result.exit_code == 0


def test_cli_main(a_test_cli):
    runner = CliRunner()
    result = runner.invoke(a_test_cli.main, ["permissions"])
    assert result.exit_code == 0

    result = runner.invoke(a_test_cli.main, ["sorter"])
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
    runner.invoke(cli.get_pattern_commands()["add"], ["test", "/(PatientID)/somepath/"])

    loaded_patterns = DicomSortCLI(configuration_file=config_file).pattern_list
    assert list(loaded_patterns.keys()) == ["idis", "nucmed", "test"]


def test_cli_dicomsort_remove_key(a_default_cli, mock_click_echo):
    """When loaded with a non-existent config file path, dicomsort CLI should create a default one
    """
    runner = CliRunner()
    runner.invoke(a_default_cli.get_pattern_commands()["remove"], ["idis"])

    loaded_patterns = DicomSortCLI(
        configuration_file=a_default_cli.configuration_file
    ).pattern_list
    assert list(loaded_patterns.keys()) == ["nucmed"]


def test_cli_dicomsort_list(a_default_cli, mock_click_echo):
    """When loaded with a non-existent config file path, dicomsort CLI should create a default one
    """
    runner = CliRunner()
    result = runner.invoke(a_default_cli.get_pattern_commands()["list"])

    assert result.exit_code == 0


def test_cli_dicomsort_dicomtags(a_default_cli, mock_click_echo):
    """List all dicomtags
    """
    runner = CliRunner()
    assert (
        runner.invoke(a_default_cli.get_pattern_commands()["list_dicomtags"]).exit_code
        == 0
    )
    assert (
        runner.invoke(
            a_default_cli.get_pattern_commands()["list_dicomtags"], ["--all"]
        ).exit_code
        == 0
    )


def test_cli_dicomsort_sort_errors(a_default_cli, mock_click_echo, folderprocessing_mock_copyfile):

    runner = CliRunner()
    result = runner.invoke(a_default_cli.get_commands()["sort"], [".", "test"])
    assert result.exit_code == 2
    assert "Unknown pattern" in result.output


def test_cli_dicomsort_sort(a_default_cli, mock_click_echo, folderprocessing_mock_copyfile):

    runner = CliRunner()
    input_path = str(RESOURCE_PATH / "adicomdir" / "folder1" / "folder1A")
    result = runner.invoke(a_default_cli.get_commands()["sort"], [input_path, "idis"], input="y\ny\ny")
    assert result.exit_code == 0
