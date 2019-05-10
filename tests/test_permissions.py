#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `trialbureautools` package."""
import pytest

from unittest.mock import patch, Mock
from click.testing import CliRunner

from icaclswrap.foldertool import WinFolderPermissionTool
from trialbureautools.cli.permissions import set_folder_permissions, create_idis_output_folder

from tests import BASE_PATH
from trialbureautools.permissions import PermissionsException, IDISOutputFolder


@pytest.fixture()
def cli_runner():
    return CliRunner()


@pytest.fixture()
def mock_set_rights(monkeypatch):
    """Make sure the set_rights method does not actually modify things on disk

    Returns
    -------
    Mock:
        the mocked function set_rights
    """
    mocked_set_rights = Mock(spec=WinFolderPermissionTool.set_rights)
    monkeypatch.setattr(
        "trialbureautools.permissions.WinFolderPermissionTool.set_rights", mocked_set_rights
    )
    return mocked_set_rights

 
@pytest.mark.parametrize(
    "path_in, username_in, permission_in, expected_output",
    [
        (
            ".",
            "crazypermission",
            "test",
            "invalid choice",
        ),  # invalid choice for permission
        (
            r"\non_existent\folder",
            "testuser",
            "full_access",
            "does not exist",
        ),  # calling on non-existent path
    ],
)
def test_set_folder_permissions_faulty_parameter_responses(
    path_in, permission_in, username_in, expected_output, cli_runner, mock_set_rights
):
    """ Commands that are wrong somehow should be handled properly by click
    """

    result = cli_runner.invoke(
        set_folder_permissions, [path_in, username_in, permission_in]
    )
    assert not mock_set_rights.called
    assert result.exit_code == 2
    assert expected_output in result.output


@pytest.mark.parametrize(
    "path_in, username_in, permission_in",
    [
        (".", "testuser", "full_access"),  # relative path
        (str(BASE_PATH), "testuser", "full_access"),  # absolute path which exists
        (str(BASE_PATH), "testuser", "read_delete"),  # other permission
    ],
)
def test_set_folder_permissions_success(
    path_in, permission_in, username_in, cli_runner, mock_set_rights
):
    """ Calling 'set_folder_permissions' an a few ways that should work'
    """

    result = cli_runner.invoke(
        set_folder_permissions, [path_in, username_in, permission_in]
    )
    assert "Set folder" in result.output
    assert mock_set_rights.called
    assert result.exit_code == 0


def test_tools_exception_handling(cli_runner, mock_set_rights):
    """ Tools might raise exceptions. These should be caught and displayed simply"""

    mock_set_rights.side_effect = PermissionsException("Something went very wrong")
    result = cli_runner.invoke(set_folder_permissions, [".", "user", "full_access"])
    assert "Something went very wrong" in result.output
    assert result.exit_code == 0


def test_create_output_folder_succes(cli_runner, mock_set_rights):
    """Test the create_idis_output_folder function the way it should work"""
    with cli_runner.isolated_filesystem():
        result = cli_runner.invoke(
            create_idis_output_folder, [".", "z123456"], input="yes"
        )
        assert not result.exception
    assert mock_set_rights.called


def test_create_output_folder_cancel(cli_runner, mock_set_rights):
    """Test the create_idis_output_folder function by cancelling halfway through """
    with cli_runner.isolated_filesystem():
        result = cli_runner.invoke(
            create_idis_output_folder, [".", "z123456"], input="no"
        )
        assert not result.exception
    assert not mock_set_rights.called


def test_create_output_folder_exception_handling(cli_runner, mock_set_rights):
    """When internal functions fail there should still be a nice string output and no stackstraces to the user """
    mock_set_rights.side_effect = PermissionsException("Terrible problem with tools")
    with cli_runner.isolated_filesystem():
        result = cli_runner.invoke(
            create_idis_output_folder, [".", "z123456"], input="yes"
        )
        assert not result.exception
    assert result.exit_code == 0
    assert 'Terrible problem with tools' in result.output


def test_create_output_folder_exception_handling(cli_runner, mock_set_rights, monkeypatch):
    """ Directory might already exist. Handle this gracefully"""
    with cli_runner.isolated_filesystem():
        def failing_mkdir(*args):
            raise FileExistsError("Exists already")

        monkeypatch.setattr('trialbureautools.permissions.os.mkdir', failing_mkdir)
        result = cli_runner.invoke(
            create_idis_output_folder, [".", "z123456"], input="yes"
        )
        assert not result.exception
    assert result.exit_code == 0
    assert 'Exists already' in result.output
