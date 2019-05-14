"""Functions for sorting DICOM paths on disk

"""
import copy
import os
from collections import UserDict, defaultdict
from pathlib import Path

import pydicom
from pydicom.errors import InvalidDicomError

from dicomsort.parser import (
    DicomPathPatternParser,
    DicomPathParseException,
    DicomTagNotFoundException,
    ResolvedPathElement,
    FolderSeparator,
)


class DicomPathPattern:
    """Describes how to generate paths for a dicom file. Can contain dicom tag or tag names. For example
    '/some_folder/(PatientID)/(0008,1030)/' is valid

    """
    parser = DicomPathPatternParser

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
        self.pattern_string = pattern_string
        try:
            parsed = self.parser().parse(pattern_string)
        except DicomPathParseException as e:
            raise DicomPathPatternException(f"Error parsing '{pattern_string}: {e}")

        self.elements = parsed

    def __str__(self):
        return self.pattern_string


class PathGenerator:
    """Describes how to generate paths for DICOM files

    """

    # if a tag value is not in a file, use this string instead
    UNKNOWN_ELEMENT_NAME = "UNKNOWN"

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
        TentativePath

        Raises
        ------
        PathGeneratorException:
            If the given file cannot be read or is not dicom

        """
        try:
            ds = pydicom.dcmread(str(path_in))
        except InvalidDicomError as e:
            raise PathGeneratorException(f"Error reading file '{path_in}': {e}")

        resolved = []
        for path_element in self.pattern.elements:
            try:
                resolved.append(path_element.resolve(ds))
            except DicomTagNotFoundException:
                resolved.append(
                    ResolvedPathElement(
                        path_element=None, resolved_value=self.UNKNOWN_ELEMENT_NAME
                    )
                )

        # group path elements by full folder or file name
        units = []

        for group in split_list(
            resolved, lambda x: type(x.path_element) == FolderSeparator
        ):
            units.append(PathUnit(group))

        return TentativePath(units)


def split_list(list_in, separator_func):
    """Split list into separate lists, using separator function. Does not include separator elements in output list.

    Parameters
    ----------
    list_in: List
        List to separate
    separator_func: func
        function(element), called on each element of list. If it evaluates to True, element is considered a separator

    Returns
    -------
    List[List]

    """

    if not list_in:
        return list_in
    split = []
    collected = []
    for element in list_in:
        if separator_func(element):
            if collected:
                split.append(collected)
                collected = []
        else:
            collected.append(element)

    if collected:
        split.append(collected)

    return split


class PathUnit:
    """Groups together one or more path elements into a single folder or file name

    So in a pattern like ../(PatientID)folder(Modality)/... there are three elements: PatientID, folder and Modality,
    but together they determine the name of a single folder. Hence they are one Unit.
    """

    def __init__(self, path_elements):
        """

        Parameters
        ----------
        path_elements: List[ResolvedPathElement]
            list of path elements in this unit
        """
        self.path_elements = path_elements

    def __str__(self):
        return self.flatten()

    def flatten(self):
        """The full resolved name for this element

        Returns
        -------
        str

        """
        return "".join([x.resolved_value for x in self.path_elements])

    def count(self):
        """Does any part of this unit indicate renaming by counting unique items?"""
        return any([x.count() for x in self.path_elements])


class TreeNode(PathUnit):
    """A folder or filename"""

    def __init__(self, path_elements, children=None, parent=None):
        """

        Parameters
        ----------
        path_elements: List[ResolvedPathElement]
        children: List[TreeNode]
        parent:TreeNode
        """
        super(TreeNode, self).__init__(path_elements)
        if not children:
            children = []
        self.children = children
        self.parent = parent

    def add(self, path_in):
        """Add the given path to this node, by converting each part of the path into a node itself
        and adding recursively

        Parameters
        ----------
        path_in: TentativePath
            Add this element to the tree

        Returns
        -------
        TreeNode:
            The final node of the added path.

        """

        node = TreeNode(path_elements=path_in.pop(0).path_elements, parent=self)
        child_map = dict(map(lambda x: (x.flatten(), x), self.children))

        if path_in.is_empty():
            # this was the last node
            if node.flatten() in child_map.keys():
                # node is already in tree as a child of current folder. Return that existing node instead
                return child_map[node.flatten()]
            else:
                # node is new. Add this node in current folder
                self.children.append(node)
                return node
        else:
            # this was not the last node. Add current element and process the rest of the path
            if node.flatten() in child_map.keys():
                # node is already in tree as a child of current folder. Add what is left to that folder
                return child_map[node.flatten()].add(path_in)
            else:
                # node is new. Add this element in current folder and process the rest
                self.children.append(node)
                return node.add(path_in)

    def flatten_full_path(self):
        """

        Returns
        -------
        str
        """

        all_path_elements = [x.flatten() for x in self.get_all_parent_elements()]
        return os.sep.join(all_path_elements)

    def get_all_parent_elements(self):
        """

        Returns
        -------
        List[PathUnit]
            This element with all its parent elements prepended
        """
        path_elements = [self]

        if self.parent:
            path_elements = self.parent.get_all_parent_elements() + path_elements

        return path_elements


class TentativePath:
    """A path that can still retains the elements that generate it so it can be changed easily

    """

    def __init__(self, units):
        """

        Parameters
        ----------
        units: List[PathUnit]
            All units that make up this path
        """
        self.units = units

    def flatten(self):
        """Give the string representation of this path

        Returns
        -------
        str
        """
        return os.sep.join([x.flatten() for x in self.units])

    def pop(self, index=-1):
        return self.units.pop(index)

    def is_empty(self):
        return not self.units


class PathMapping(UserDict):

    def get_overlapping(self):
        """Check whether there are files that map to the same location. If so, return a list of original files mapping
         to the same location

         Returns
         -------
         Dict[str, List[]]
            For each group of orginal files mapping to the same output file, that file and the list of original files.
         """

        mapping = self.as_flat_dict()
        reverse_mapping = defaultdict(list)
        for key, value in mapping.items():
            reverse_mapping[value].append(key)

        duplicate_maps = {x: y for x, y in reverse_mapping.items() if len(y) > 1}
        return duplicate_maps

    def as_flat_dict(self):
        """Flatten the resolved elements to string for each mapped file path

        Returns
        -------
        Dict[Path:Path]

        """
        raise NotImplementedError()


class UserPathMapping(PathMapping):
    """A simple mapping that can be created without any parsing. Internally holds only a flat dict Path:Path

    """

    def __init__(self, mapping=None):
        """

        Parameters
        ----------
        mapping: Dict[Path:Path]
            input dict
        """
        if not mapping:
            mapping = {}
        self.data = mapping

    def as_flat_dict(self):
        return self.data


class StraightPathMapping(PathMapping):
    """A dictionary-like object mapping from each input path to TentativePath: a path that retains its elements for
    easy manipulation later

    Dict[Path:TentativePath]

    """

    def __init__(self, mapping=None):
        if not mapping:
            mapping = {}
        self.data = mapping

    def as_flat_dict(self):
        """Flatten the resolved elements to string for each mapped file path

        Returns
        -------
        Dict[Path:Path]

        """
        flat_dict = {}
        for org_path, tentative_path in self.data.items():
            flat_dict[org_path] = Path(tentative_path.flatten())
        return flat_dict

    def as_tree(self):
        """This path mapping as a tree structure

        Returns
        -------
        PathTreeMapping
        """
        tree_mapping = PathTreeMapping()

        for org_path, path in self.data.items():
            tree_mapping[org_path] = tree_mapping.add(copy.deepcopy(path))
        return tree_mapping


class PathTreeMapping(PathMapping):
    """A dictionary-like object mapping from each input path to each potential

    Dict[Path:TentativePath]

    """

    def __init__(self, root=None):
        """

        Parameters
        ----------

        root: TreeNode, optional
            Root node for this tree. Defaults to an empty TreeNode
        """
        if not root:
            root = TreeNode(path_elements=[], children=[])
        self.root = root
        self.data = {}

    def as_flat_dict(self):
        """Flatten the resolved elements to string for each mapped file path

        Returns
        -------
        Dict[Path:Path]

        """
        flat = {}
        for path, end_node in self.data.items():
            all_nodes_for_path = end_node.get_all_parent_elements()[
                1:
            ]  # discard empty root node
            flat[path] = Path(os.sep.join([x.flatten() for x in all_nodes_for_path]))
        return flat

    def add(self, path):
        """Add the given path to this tree, creating new nodes if needed, using existing if possible

        Parameters
        ----------
        path: TentativePath


        Returns
        -------
        TreeNode:
            The final node of the added path.

        """
        return self.root.add(path)

    def apply_count(self, node=None):
        """If children of node have .count=True, rename them by counting unique values in single folder.

        See docs for VariableElement for more info on counting

        Parameters
        ----------
        node: TreeNode, optional
            the node whose children to count. Defaults to this tree's root node.


        Returns
        -------
        PathTreeMapping:
            This tree after all values for path elements with count=True have been replaced by counting unique values in
            a single folder

        """
        if not node:
            node = self.root

        # all children should be generated by the same collection of path_elements. Collect these
        if node.children:
            path_elements_for_all_children = defaultdict(list)
            for child in node.children:
                for idx, element in enumerate(child.path_elements):
                    path_elements_for_all_children[idx].append(element)

            # count per element
            for elementlist in path_elements_for_all_children.values():
                if elementlist[0].count():  # this element should be counted
                    # create mapping of unique values to count
                    # string_length: use 0,1,2,.. for up to 9 values, use 00,01,02,.. for up to 99, etc..
                    string_length = len(str(len(elementlist)))
                    mapping = {
                        org: format(idx, "0" + str(string_length))
                        for idx, org in enumerate(
                            set([x.resolved_value for x in elementlist])
                        )
                    }
                    for element in elementlist:
                        element.resolved_value = mapping[element.resolved_value]

        # make PathTreeMapping of each child and repeat
        for child in node.children:
            self.apply_count(child)

    def as_tree(self):
        return self


class DicomPathPatternException(Exception):
    pass


class PathGeneratorException(Exception):
    pass


class PathCountException(Exception):
    pass
