# -*- coding: utf-8 -*-

""" Python functions that could be of use for the trial bureau.

Docstrings in this module are for programmers, so can be as detailed is needed """
import os

from icaclswrap.foldertool import WinFolderPermissionTool, ACLToolException

from icaclswrap.rights import FULL_ACCESS, READ_DELETE

PERMISSIONS = {'full_access': FULL_ACCESS,
               'read_delete': READ_DELETE}


def set_folder_rights(folder, username, permission):
    """Set permissions from given

    Parameters
    ----------
    folder: path
        path to set permissions for. Can be relative or absolute
    username: str
        username to set permissions for
    permission: str
        choice of any of trialbureautools.permissions.PERMISSIONS

    Raises
    ------
    PermissionsException
        when anything goes wrong with setting folder rights

    """

    tool = WinFolderPermissionTool()
    try:
        tool.set_rights(path=folder, username=username, rights_collection=permission)
    except ACLToolException as e:
        raise PermissionsException(str(e))


class IDISOutputFolder:

    def __init__(self, base_folder, z_number):
        """Create z-number folder and set permissions

        Parameters
        ----------
        base_folder: Path
            create folder in this path
        z_number: str
            valid radboudumc z-number, like z123456

        Raises
        ------
        PermissionsException
            when anything goes wrong with setting folder rights

        """

        self.z_number = z_number
        self.path = str(base_folder / z_number)
        self.initialized = False
        self.permission = READ_DELETE

    def initialize(self):
        try:
            os.mkdir(self.path)
        except FileExistsError as e:
            raise PermissionsException(str(e))
        set_folder_rights(folder=self.path, username=self.z_number, permission=self.permission)


class PermissionsException(Exception):
    pass
