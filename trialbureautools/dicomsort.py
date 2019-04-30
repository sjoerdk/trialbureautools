"""Functions for sorting DICOM paths on disk

"""

from collections import UserDict
from pathlib import Path

import pydicom

from trialbureautools.parser import DicomPathPatternParser, DicomPathParseException, DicomTagNotFoundException


class DicomPathPattern:
    """Describes how to generate paths for a dicom file. Can contain dicom tag or tag names. For example
    '/some_folder/(PatientID)/(0008,1030)/' is valid

    """

    def __init__(self, pattern_string):
        """
        Parameters
        ----------
        pattern_string: str

        Returns
        -------
        List[DicomPathElement]:
            List with different DicomPathElements for each string literal, dicom tag or dicom tag name

        Raises
        ------
        DicomPathPatternException:
            If pattern_string cannot be parsed to a list of strings and valid dicom tags
        """
        try:
            parsed = DicomPathPatternParser().parse(pattern_string)
        except DicomPathParseException as e:
            raise DicomPathPatternException(f"Error parsing '{pattern_string}: {e}")

        self.elements = parsed




class PathGenerator:
    """Describes how to generate paths for DICOM files

    """
    # if a tag value is not in a file, use this string instead
    UNKNOWN_FOLDER_NAME = 'UNKNOWN'

    def __init__(self, pattern):
        """

        Parameters
        ----------
        pattern: DicomPathPattern
        """
        # check pattern validity
        self.pattern = pattern

    def generate(self, path_in):
        """Generate a path for the given file

        Parameters
        ----------
        path_in: Path

        Returns
        -------
        Path

        """

        ds = pydicom.dcmread(str(path_in))
        path = ""
        for path_element in self.pattern.elements:
            try:
                resolved = path_element.resolve(ds)
            except DicomTagNotFoundException:
                resolved = self.UNKNOWN_FOLDER_NAME
            path += resolved

        return path


class PathMapper:
    """Maps old paths to new paths given a certain pattern

    """

    def __init__(self, generator):
        """

        Parameters
        ----------
        generator: PathGenerator
        """
        self.generator = generator

    def map(self, paths):
        """

        Parameters
        ----------
        paths: List[Path]

        Returns
        -------
        PathMapping

        """
        mapping = PathMapping()
        for path in paths:
            mapping[path] = self.generator.generate(path)
        return mapping


class PathMapping(UserDict):
    """A dictionary-like object mapping from each input path to each output path

    """

    def __init__(self, mapping=None):
        if not mapping:
            mapping = {}
        self.data = mapping


class DicomPathPatternException(Exception):
    pass
