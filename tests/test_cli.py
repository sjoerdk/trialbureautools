#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `trialbureautools` package."""
import pytest

from unittest.mock import patch
from click.testing import CliRunner

from icaclswrap.foldertool import WinFolderPermissionTool
from trialbureautools.cli import set_folder_permissions, create_idis_output_folder

from tests import BASE_PATH
from trialbureautools.tools import ToolsException, IDISOutputFolder


@pytest.fixture()
def cli_runner():
    return CliRunner()


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
    path_in, permission_in, username_in, expected_output, cli_runner
):
    """ Commands that are wrong somehow should be handled properly by click
    """
    with patch.object(WinFolderPermissionTool, "set_rights") as mock_set_rights:
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
        (str(BASE_PATH), "testuser", "full_access"),  # absolute path ,
        (str(BASE_PATH), "testuser", "read_delete"),  # other permission ,
    ],
)
def test_set_folder_permissions_success(
    path_in, permission_in, username_in, cli_runner
):
    """ Calling 'set_folder_permissions' an a few ways that should work'
    """
    with patch(
        "trialbureautools.tools.WinFolderPermissionTool.set_rights", autospec=True
    ) as mock_set_rights:
        result = cli_runner.invoke(
            set_folder_permissions, [path_in, username_in, permission_in]
        )
    assert "Set folder" in result.output
    assert mock_set_rights.called
    assert result.exit_code == 0


def test_tools_exception_handling(cli_runner):
    """ Tools might raise exceptions. These should be caught and displayed simply"""

    with patch(
        "trialbureautools.tools.WinFolderPermissionTool.set_rights", autospec=True
    ) as mock_set_rights:
        mock_set_rights.side_effect = ToolsException("Something went very wrong")
        result = cli_runner.invoke(set_folder_permissions, [".", "user", "full_access"])
        assert "Something went very wrong" in result.output
        assert result.exit_code == 0


def test_create_CLI_function(cli_runner):
    with patch(
        "trialbureautools.tools.WinFolderPermissionTool.set_rights", autospec=True
    ) as mock_set_rights:
        with cli_runner.isolated_filesystem():
            result = cli_runner.invoke(
                create_idis_output_folder, [".", "z123456"], input="yes"
            )
            assert not result.exception
        assert mock_set_rights.called
