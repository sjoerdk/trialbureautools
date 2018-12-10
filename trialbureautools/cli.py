# -*- coding: utf-8 -*-

"""Command line interface for trialbureautools. Exposes functions from the 'tools' module. This module should not
contain important functionality but rather just define the command line interface.

docstrings in this module are displayed by the click CLI so should be user-centered."""

import sys
from pathlib import Path

import click

from trialbureautools.tools import set_folder_rights, PERMISSIONS, ToolsException, IDISOutputFolder


@click.group()
def cli():
    """Trial bureau scripts"""
    pass


@click.command(short_help="Set folder permissions")
@click.argument('folder', type=click.Path(exists=True, resolve_path=True))
@click.argument('username', type=str)
@click.argument('permission_name', type=click.Choice(list(PERMISSIONS.keys())))
def set_folder_permissions(folder, username, permission_name):
    """Set permissions for given windows folder and windows user

    Example:

        set_folder_permissions C:\folder1 z123456 full_access\b

        sets the permissions for C:\folder1 so that user 'z123456' has full access

    """
    try:
        set_folder_rights(folder=folder, username=username, permission=PERMISSIONS[permission_name])
        click.echo(f"Set folder '{folder}' permissions to {permission_name}")
    except ToolsException as e:
        click.echo(f'Error: { str(e) }')


@click.command(short_help="Create an IDIS output folder in the given folder")
@click.argument('base_folder', type=click.Path(exists=True, resolve_path=True))
@click.argument('z_number', type=str)
def create_idis_output_folder(base_folder, z_number):
    """Create an IDIS output folder in the given folder with permissions to read and delete but not write

        Example:

        create_idis_output_folder . z123456

        creates a folder 'z123456' in the current directory, and sets permissions
    """
    folder = IDISOutputFolder(base_folder=Path(base_folder), z_number=z_number)
    if click.confirm(f'This will create an IDIS output folder in "{folder.path}"'):
        try:
            folder.initialize()
            click.echo(f'Done')
        except ToolsException as e:
            click.echo(f'Error: { str(e) }')
    else:
        click.echo("cancelled")


cli.add_command(set_folder_permissions)
cli.add_command(create_idis_output_folder)

if __name__ == "__main__":
    sys.exit(cli())  # pragma: no cover
