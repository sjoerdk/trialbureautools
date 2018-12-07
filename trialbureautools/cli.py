# -*- coding: utf-8 -*-

"""Console script for trialbureautools."""
import sys
import click
from icaclswrap.foldertool import WinFolderPermissionTool

from icaclswrap.rights import FULL_ACCESS, READ_DELETE

PERMISSIONS = {'full_access': FULL_ACCESS,
               'read_delete': READ_DELETE}


@click.group()
def cli():
    pass


@click.command()
@click.argument('folder', type=click.Path(exists=True, resolve_path=True))
@click.argument('username', type=str)
@click.argument('permission_name', type=click.Choice(list(PERMISSIONS.keys())))
def set_folder_permissions(folder, username, permission_name):
    """Set permissions from given

    Parameters
    ----------
    folder: path
        path to set permissions for. Can be relative or absolute
    username: str
        username to set permissions for
    permission_name: str
        choice of any of trialbureautools.permissions.PERMISSIONS

    """
    tool = WinFolderPermissionTool()
    tool.set_rights(path=folder, username=username, rights_collection=PERMISSIONS[permission_name])
    click.echo(f"Set folder '{folder}' permissions to {permission_name}")


@click.command()
def say_hello():
    print("Hello")


cli.add_command(set_folder_permissions)
cli.add_command(say_hello)

if __name__ == "__main__":
    sys.exit(cli())  # pragma: no cover
