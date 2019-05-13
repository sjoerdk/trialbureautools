# -*- coding: utf-8 -*-

"""Main command line interface for trialbureautools
"""

from pathlib import Path

import click

from trialbureautools.cli.dicomsort import DicomSortCLI
from trialbureautools.cli.permissions import set_folder_permissions, create_idis_output_folder


class TrialBureauToolsCLI:
    def __init__(self, config_path):
        """

        Parameters
        ----------
        config_path: Path
            path to folder that contains config files

        """
        self.config_path = config_path
        self.assert_path(self.config_path)

        self.main.add_command(self.permissions)

        self.permissions.add_command(set_folder_permissions)
        self.permissions.add_command(create_idis_output_folder)

        self.sort_cli = DicomSortCLI(self.config_path / "dicom_sort_paths.yaml")
        for command in self.sort_cli.get_commands().values():
            self.sorter.add_command(command)

        self.main.add_command(self.sorter)

    @staticmethod
    def assert_path(path: Path):
        """Create path if does not exist

        """
        try:
            path.mkdir(parents=True, exist_ok=False)
        except FileExistsError:
            pass

    @staticmethod
    @click.group()
    def main():
        """Trial bureau scripts"""
        pass

    @staticmethod
    @click.group()
    def permissions():
        """Work with windows folder permissions """
        pass

    @staticmethod
    @click.group()
    def sorter():
        """Sort DICOM Files based on tag values  """
        pass


cli = TrialBureauToolsCLI(config_path=Path.home() / "tbt_config").main
