# -*- coding: utf-8 -*-

"""Command line interface for trialbureautools. Exposes functions from the 'tools' module. This module should not
contain important functionality but rather just define the command line interface.

docstrings in this module are displayed by the click CLI so should be user-centered."""

import sys
import click

from trialbureautools.tools import set_folder_rights, PERMISSIONS, ToolsException


@click.group()
def cli():
    pass


@click.command()
@click.argument('folder', type=click.Path(exists=True, resolve_path=True))
@click.argument('username', type=str)
@click.argument('permission_name', type=click.Choice(list(PERMISSIONS.keys())))
def set_folder_permissions(folder, username, permission_name):
    """Set permissions for given folder and user

    """
    try:
        set_folder_rights(folder=folder, username=username, permission_name=permission_name)
        click.echo(f"Set folder '{folder}' permissions to {permission_name}")
    except ToolsException as e:
        click.echo(f'Error: { str(e) }')


@click.command()
def say_hello():
    print("Hello")


cli.add_command(set_folder_permissions)
cli.add_command(say_hello)

if __name__ == "__main__":
    sys.exit(cli())  # pragma: no cover