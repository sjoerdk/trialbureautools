import collections
from os import PathLike, path

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
        with open(path, "w") as f:
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
        """

        Parameters
        ----------
        path: PathLike
            Load from this path

        Returns
        -------
        DicomPathPatterns

        """
        with open(path, "r") as f:
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
        super(SerializableDicomPathPattern, self).__init__(
            pattern_string=pattern_string
        )

    def as_dict(self):
        return {"pattern": self.pattern_string}

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
        self.active_pattern = None

    @staticmethod
    def assert_configuration_file(file_path):
        """Create a default configuration file if one does not exist

        Parameters
        ----------
        file_path: str
            Path to configuration file

        """
        if not file_path.exists():
            click.echo(
                f"Settings file '{file_path}' did not exist. Writing default contents."
            )
            DefaultPatternsList().save(file_path)

    def save(self):
        """Save patterns to file"""
        self.pattern_list.save(self.configuration_file)

    def get_commands(self):
        """

        Returns
        -------
        Dict[str, click.command], command_name : click command that can be added with add_command()

        """

        @click.command()
        @click.argument('input_dir', type=click.Path(exists=True))
        @click.argument('pattern')
        @click.option('--output_dir', type=click.Path(), help="Write sorted files into the given directory")
        def sort(input_dir, pattern, output_dir):
            """Sort all dicom files in given directory

            """

            input_dir_abs = path.abspath(input_dir)
            pattern = self.pattern_list[pattern]
            click.echo(f"sorting {input_dir_abs} with {pattern}, writing to {output_dir}")

        return {
            "sort": sort
        }

    def get_status_command(self):

        @click.command(short_help='Show current settings')
        def status(self):
            self.pattern_string

    def get_admin_commands(self):
        """

        Returns
        -------
        Dict[str, click.command], command_name : click command that can be added with add_command()

        """

        @click.command(short_help="List all patterns")
        def list():
            """list all DICOM path patterns"""
            for key, value in self.pattern_list.as_flat_dict().items():
                click.echo(f"{key}: {value}")

        @click.command(short_help="Add given pattern and save to file")
        @click.argument("key")
        @click.argument("pattern_string")
        def add_pattern(key, pattern_string):
            """Add a DICOM path pattern under a certain key

            Usage: add_pattern <key> <pattern>

            <Key> Should be a short description without spaces. like 'ct' or 'flat' (without the parenthesis).

            <pattern> Should be a valid DICOM path pattern like '/folder/(PatientID)/(count:StudyInstanceUID)' -(again, without parenthesis)
            """
            self.pattern_list.add_pattern(key, pattern_string)
            self.save()

        @click.command(short_help="Remove given pattern and save to file")
        @click.argument("key")
        def remove_pattern(key):
            """Remove the pattern by key. To see all keys use the list command
            """
            try:
                self.pattern_list.pop(key)
                self.save()
            except KeyError:
                click.echo(f"Key {key} does not exist in this list")

        @click.command()
        @click.option(
            "--all",
            "a",
            is_flag=True,
            default=False,
            help="Show all 4000+ accepted tags. Else show only most useful",
        )
        def dicomtags(a):
            """list all valid dicomtag names and numbers"""

            most_useful = [
                "SOPClassUID",
                "SOPInstanceUID",
                "StudyDate",
                "SeriesDate",
                "AcquisitionDate",
                "Modality",
                "PatientID",
                "PatientName",
                "DeviceID",
                "StudyInstanceUID",
                "SeriesInstanceUID",
                "StudyID",
                "SeriesNumber",
                "InstanceNumber",
            ]

            all_names = DicomPathPattern.parser.valid_dicom_tag_names()
            if a:
                title = f"All {len(all_names)} accepted tags"
                names = all_names
            else:
                title = f'{len(most_useful)} most useful tags. To show all len{len(all_names)} use "dicomtags --all"'
                names = [(name, tag) for name, tag in all_names if name in most_useful]

            click.echo("-" * len(title))
            click.echo(title)
            click.echo("-"*len(title))
            click.echo("\n".join([f"{x} - {y}" for x, y in names]))

        return {
            "add_pattern": add_pattern,
            "remove_pattern": remove_pattern,
            "dicomtags": dicomtags,
            "list": list
        }


class DefaultPatternsList(DicomPathPatterns):
    """A Dicom Patterns list with some default content

    """

    default_patterns = {
        "idis": "(0010,0020)/(0008,1030)-(0008,0050)/(0008,103e)-(0008,0060)-(0020,0011)/(count:SOPInstanceUID)",
        "nucmed": "(0010,0020)/(0008,1030)-(0008,0050)/(0008,0020)/(0008,103e)-(0008,0060)-(0020,0011)"
        "/(count:SOPInstanceUID)",
    }

    def __init__(self):
        super(DefaultPatternsList, self).__init__(flat_dict=self.default_patterns)


class DicomSortCLIException(Exception):
    pass
