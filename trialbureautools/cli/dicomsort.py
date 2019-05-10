import collections
from os import PathLike

import click
import yaml

from dicomsort.core import DicomPathPattern
from collections import UserDict


class DicomPathPatterns(UserDict):
    """Dict-like collection of PersistableDicomPathPatterns

    Dict[key: pattern_string]
    """
    def __init__(self, flat_dict=None):
        """

        Parameters
        ----------
        flat_dict: Dict[str: str]
            initial contents given as key:dicompathstring.

        """
        if not flat_dict:
            flat_dict = {}
        object_dict = {}
        for key, pathstring in flat_dict.items():
            object_dict[key] = SerializableDicomPathPattern(pattern_string=pathstring)

        super(DicomPathPatterns, self).__init__(object_dict)

    def save(self, path):
        with open(path, 'w') as f:
            yaml.dump(self.as_flat_dict(), f, default_flow_style=False)
        click.echo(f"Saved patterns to {path}")

    def as_flat_dict(self):
        """This collection as a key: pattern_string dict

        Returns
        -------
        Dict[str,str]
        """
        return {key: item.pattern_string for key, item in self.items()}

    @classmethod
    def load(cls, path):
        with open(path, 'r') as f:
            flat_dict = yaml.safe_load(f)
        return cls(flat_dict=flat_dict)

    def add_pattern(self, key, pattern_string):
        """

        Parameters
        ----------
        key: str
            Short key for this pattern
        pattern_string: str
            Dicom Path pattern string

        """
        self.data[key] = SerializableDicomPathPattern(pattern_string=pattern_string)


class SerializableDicomPathPattern(DicomPathPattern):
    """A DicomPathPattern that can be saved and loaded from and to dict """

    def __init__(self, pattern_string):
        super(SerializableDicomPathPattern, self).__init__(pattern_string=pattern_string)

    def as_dict(self):
        return {'pattern': self.pattern_string}

    @staticmethod
    def from_dict(dict_in):
        """

        Parameters
        ----------
        dict_in: Dict
            Dict for constructing this item. For elements see output of as_dict

        Returns
        -------
        SerializableDicomPathPattern

        """
        pass


class DicomSortCLI:

    def __init__(self, configuration_file: PathLike):
        self.assert_configuration_file(configuration_file)
        self.configuration_file = configuration_file
        self.pattern_list = DicomPathPatterns.load(configuration_file)

    @staticmethod
    def assert_configuration_file(file_path):
        """Create a default configuration file if one does not exist

        Parameters
        ----------
        file_path: str
            Path to configuration file

        """
        if not file_path.exists():
            click.echo(f"Settings file '{file_path}' did not exist. Writing default contents.")
            DefaultPatternsList().save(file_path)

    def save(self):
        """Save patterns to file"""
        self.pattern_list.save(self.configuration_file)

    def get_click_commands(self):
        """

        Returns
        -------
        Dict[str, click.command], command_name : click command that can be added with add_command()

        """

        @click.command()
        @click.argument('key')
        @click.argument('pattern_string')
        def add_pattern(key, pattern_string):
            """Add given pattern and save to file
            """
            self.pattern_list.add_pattern(key, pattern_string)
            self.save()

        @click.command()
        @click.argument('key')
        def remove_pattern(key):
            """remove given pattern and save to file
            """
            try:
                self.pattern_list.pop(key)
                self.save()
            except KeyError:
                click.echo(f"Key {key} does not exist in this list")

        @click.command()
        def list():
            """list all patterns """
            for key, value in self.pattern_list.as_flat_dict().items():
                click.echo(f"{key}: {value}")

        return {'add_pattern': add_pattern, 'remove_pattern': remove_pattern, 'list': list}

        
class DefaultPatternsList(DicomPathPatterns):
    """A Dicom Patterns list with some default content

    """
    default_patterns = {
        'idis': '(0010,0020)/(0008,1030)-(0008,0050)/(0008,103e)-(0008,0060)-(0020,0011)/(count:SOPInstanceUID)',
        'nucmed': '(0010,0020)/(0008,1030)-(0008,0050)/(0008,0020)/(0008,103e)-(0008,0060)-(0020,0011)'
                  '/(count:SOPInstanceUID)'
    }

    def __init__(self):
        super(DefaultPatternsList, self).__init__(flat_dict=self.default_patterns)


class DicomSortCLIException(Exception):
    pass
