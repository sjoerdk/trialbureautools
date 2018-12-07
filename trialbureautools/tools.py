# -*- coding: utf-8 -*-

""" Python functions that could be of use for the trial bureau """
from icaclswrap.foldertool import WinFolderPermissionTool

from icaclswrap.rights import FULL_ACCESS, READ_DELETE

PERMISSIONS = {'full_access': FULL_ACCESS,
               'read_delete': READ_DELETE}


def set_folder_rights(folder, username, permission_name):
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
