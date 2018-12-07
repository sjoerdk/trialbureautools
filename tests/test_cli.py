#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `trialbureautools` package."""
import pytest

from unittest.mock import patch
from click.testing import CliRunner

from icaclswrap.foldertool import WinFolderPermissionTool
from trialbureautools.cli import set_folder_permissions

from tests import BASE_PATH


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
    path_in, permission_in, username_in, expected_output
):
    """ Commands that are wrong somehow should be handled properly by click
    """
    runner = CliRunner()
    with patch.object(WinFolderPermissionTool, "set_rights") as mock_set_rights:
        result = runner.invoke(
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
    path_in, permission_in, username_in
):
    """ Calling 'set_folder_permissions' an a few ways that should work'
    """
    runner = CliRunner()
    with patch(
        "trialbureautools.tools.WinFolderPermissionTool.set_rights", autospec=True
    ) as mock_set_rights:
        result = runner.invoke(
            set_folder_permissions, [path_in, username_in, permission_in]
        )
    assert "Set folder" in result.output
    assert mock_set_rights.called
    assert result.exit_code == 0


