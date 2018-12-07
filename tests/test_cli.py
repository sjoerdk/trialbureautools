#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `trialbureautools` package."""
from unittest.mock import patch, create_autospec

import pytest

from click.testing import CliRunner
from icaclswrap.foldertool import WinFolderPermissionTool

from trialbureautools.cli import set_folder_permissions


@pytest.mark.parametrize(
    "path_in, username_in, permission_in, expected_output",
    [
        (".", "testuser", "test", "invalid choice"),
        (r"\non_existing\folder", "testuser", "full_access", "does not exist"),
    ],
)
def test_command_line_interface_fails(
    path_in, permission_in, username_in, expected_output
):
    runner = CliRunner()
    with patch.object(WinFolderPermissionTool, 'set_rights') as mock_set_rights:
        result = runner.invoke(set_folder_permissions, [path_in, username_in, permission_in])
    assert not mock_set_rights.called
    assert result.exit_code == 2
    assert expected_output in result.output


@pytest.mark.parametrize(
    "path_in, username_in, permission_in, expected_output",
    [
        (".", "testuser", "full_access", "Set folder"),
    ],
)
def test_command_line_interface_succes(
    path_in, permission_in, username_in, expected_output
):
    runner = CliRunner()
    with patch('trialbureautools.cli.WinFolderPermissionTool.set_rights', autospec=True) as mock_set_rights:
        result = runner.invoke(set_folder_permissions, [path_in, username_in, permission_in])
    assert expected_output in result.output
    assert mock_set_rights.called
    assert result.exit_code == 0



