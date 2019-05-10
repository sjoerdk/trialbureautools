from pathlib import Path

import click

from trialbureautools.permissions import PERMISSIONS, set_folder_rights, PermissionsException, IDISOutputFolder


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
    except PermissionsException as e:
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
            click.echo(f'Created folder {folder.path} with permissions: {folder.permission.description}')
        except PermissionsException as e:
            click.echo(f'Error: { str(e) }')
    else:
        click.echo("cancelled")
