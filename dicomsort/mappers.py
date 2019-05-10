"""A mapper takes a list of files and generates new paths for each one, given a certain pattern

"""
import os

from dicomsort.core import StraightPathMapping, PathGeneratorException, DicomPathPattern, PathGenerator


class PathMapper:
    """Maps old paths to new paths given a generator

    """

    def __init__(self, generator):
        self.generator = generator

    def map(self, paths):
        """For each path in paths, generate a new path

        Parameters
        ----------
        paths: List[Path]

        Returns
        -------
        PathMapping

        """
        raise NotImplementedError()


class StraightPathMapper(PathMapper):
    """Maps old paths to new paths given a certain pattern. Maps in a straight way without counting or checking
    duplicates

    """

    def __init__(self, generator):
        """

        Parameters
        ----------
        generator: PathGenerator
        """
        super(StraightPathMapper, self).__init__(generator)

    def map(self, paths):
        """

        Parameters
        ----------
        paths: List[Path]

        Returns
        -------
        StraightPathMapping

        """
        mapping = StraightPathMapping()
        paths_ignored_dicom_error = []
        for path in paths:
            try:
                new_path = self.generator.generate(path)
                mapping[path] = new_path
            except PathGeneratorException:
                paths_ignored_dicom_error.append(path)

        return mapping


class FullPathMapper(PathMapper):
    """Maps old paths to new paths given a certain pattern. Does counting of countable elements and raises errors
    for potential overwriting and paths that would be too long for windows

    """

    WINDOWS_PATH_LENGTH_LIMIT = 260

    def __init__(self, pattern, root_path=None, check_path_lengths=True):
        """

        Parameters
        ----------
        pattern: str
            Path pattern string to generate new paths with
        root_path: str, optional
            Prepend this path to all generated paths. Defaults to None, which means paths will be generated exactly
            as described in pattern
        check_path_lengths: str, optional
            If true, raise exception if any mapped path is longer then windows max path length. defaults to True

        """
        self.root_path = root_path
        if self.root_path:
            pattern = os.path.normpath(str(self.root_path) + os.sep + pattern)
        super(FullPathMapper, self).__init__(PathGenerator(DicomPathPattern(pattern)))

        self.check_path_lengths = check_path_lengths

    def map(self, paths):
        """Map each path to its output path. Check for several potential problems

        Parameters
        ----------
        paths: List[Path]

        Raises
        ------
        OverlappingFilePathException(MappingException):
            When mapped paths overlap, which would cause existing files to be overwritten

        PathTooLongForWindowsException(MappingException):
            When any path is longer then windows max file path length. Raised only if self.check_path_lengths = True

        UnsafeMappingException(MappingException):
            When any of the output paths equals any of the input paths. This means executing this mapping would
            overwrite part of the input

        Returns
        -------
        PathTreeMapping

        """
        straight_mapper = StraightPathMapper(self.generator)
        mapped = straight_mapper.map(paths)
        tree = mapped.as_tree()
        tree.apply_count()
        overlapping = tree.get_overlapping()

        if overlapping:
            msg = f"There were {len(overlapping.keys())} cases where files would be overwritten. Showing output " \
                f"paths followed by all original paths mapping to that path: {overlapping}"
            raise OverlappingFilePathException(msg)

        flat = tree.as_flat_dict()
        for original, mapped in flat.items():
            if mapped in flat.keys():
                msg = f"mapping {str(original)} -> {str(mapped)} maps to a file in the input files. Exectuting this" \
                      f"mapping would corrupt the input files"
                raise UnsafeMappingException(msg)

        if self.check_path_lengths:
            problematic_in_windows = {x: y for x, y in tree.as_flat_dict().items() if
                                      len(str(y)) > self.WINDOWS_PATH_LENGTH_LIMIT}
            if problematic_in_windows:
                msg = f"Mapping contains {len(problematic_in_windows)} paths that are longer then" \
                    f" {self.WINDOWS_PATH_LENGTH_LIMIT} characters. This might cause problems in certain windows systems"
                raise PathTooLongForWindowsException(msg)

        return tree


class MappingException(Exception):
    pass


class UnsafeMappingException(MappingException):
    pass


class OverlappingFilePathException(MappingException):
    pass


class PathTooLongForWindowsException(MappingException):
    pass
