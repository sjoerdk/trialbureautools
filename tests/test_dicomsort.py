#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from pathlib import Path

import pytest
from tests import RESOURCE_PATH
from trialbureautools.dicomsort import (
    StraightPathMapper,
    PathGenerator,
    DicomPathPattern,
    DicomPathPatternException,
    split_list,
    FullPathMapper)
from trialbureautools.parser import (
    FolderSeparator,
    DicomTag,
    StringLiteral,
    ResolvedPathElement,
)


@pytest.fixture
def some_dicom_files():
    dicom_dir = RESOURCE_PATH / "adicomdir"
    files = [x for x in dicom_dir.glob("**/*") if x.is_file()]
    return files


@pytest.fixture
def some_more_dicom_files():
    dicom_dir = RESOURCE_PATH / "anotherdicomdir"
    files = [x for x in dicom_dir.glob("**/*") if x.is_file()]
    return files


def test_dicom_sort(some_dicom_files):
    """ Check whether files are mapped to expected new locations"""

    # map all files to a single string, bit silly, but possible
    sorter = StraightPathMapper(PathGenerator(DicomPathPattern("kees")))
    mapped = sorter.map(some_dicom_files).as_flat_dict()
    assert set(mapped.values()) == {"kees"}

    sorter = StraightPathMapper(
        PathGenerator(DicomPathPattern("(PatientID)/thing/(SOPInstanceUID)"))
    )
    mapped = sorter.map(some_dicom_files).as_flat_dict()
    assert set(mapped.values()) == {
        os.sep.join(["300034001", "thing", "1.3.6.1.4.1.25403.345051766658.5228.20160418093524.118"]),
        os.sep.join(["282497552115908864921858108877181315664", "thing" ,"1.3.6.1.4.1.14519.5.2.1.9999.9999.100715157022399267532658753333"]),
    }


def test_dicom_mapped_as_tree(some_more_dicom_files):
    """ Check mapping of tentative paths as tree"""

    pattern = DicomPathPattern(
        "(PatientID)/(0008,0060)-study(StudyDescription)/(SeriesDescription)/(SOPInstanceUID)"
    )
    sorter = StraightPathMapper(PathGenerator(pattern))
    mapped = sorter.map(some_more_dicom_files)
    tree = mapped.as_tree()
    tree_flat = tree.as_flat_dict()
    mapped_flat = mapped.as_flat_dict()
    for key in mapped_flat.keys():
        assert mapped_flat[key] == tree_flat[key]


def test_dicom_sort_count(some_more_dicom_files):
    """ Check the count functionality, which will replace a variable part of the pattern with a number based
    on the number of unique elements int that folder"""

    pattern = DicomPathPattern(
        "(PatientID)/(0008,0060)-study(count:StudyDescription)/(SeriesDescription)/file(count:SOPInstanceUID)"
    )
    sorter = StraightPathMapper(PathGenerator(pattern))
    tree = sorter.map(some_more_dicom_files).as_tree()
    tree.apply_count()
    mapping = tree.as_flat_dict()
    final = sorted(list(mapping.values()))
    assert final[0] == os.sep.join(["test0430", "CT-study0", "2.0", "file0"])
    assert final[6] == os.sep.join(["test0430", "CT-study0", "AiCE_3.000_CE", "file04"])


def test_dicom_sort_overlapping_filenames_warning(some_more_dicom_files):
    """ When path mapping is not specific enough it is very well possible that multiple files are mapped to
    the location. Files should never be overwritten, so this is an error """


    pattern = DicomPathPattern(
        "(PatientID)/(0008,0060)-study(count:StudyDescription)/(SeriesDescription)/file"
    )
    sorter = StraightPathMapper(PathGenerator(pattern))
    tree = sorter.map(some_more_dicom_files).as_tree()
    tree.apply_count()
    overlapping = tree.get_overlapping()
    assert len(overlapping) == 2


def test_full_path_mapper(some_more_dicom_files):
    pattern = DicomPathPattern(
        "(PatientID)/(0008,0060)-study(count:StudyDescription)/(SeriesDescription)/file(count:SOPInstanceUID)"
    )
    mapper = FullPathMapper(PathGenerator(pattern))
    tree = mapper.map(some_more_dicom_files)
    test =1


def test_split_list():
    separator = DicomPathPattern("foo")
    element = DicomTag(tag_code="1234,5676")
    alist = [separator, element, element, separator, element]

    split = split_list(alist, lambda x: x == separator)
    assert len(split) == 2
    assert len(split[0]) == 2
    assert len(split[1]) == 1

    anotherlist = [separator, element, element, separator, element, separator, separator]
    split = split_list(alist, lambda x: x == separator)
    assert len(split) == 2
    assert len(split[0]) == 2
    assert len(split[1]) == 1

    assert split_list([separator], lambda x: x == separator) == []

    split = split_list([None, 3, 4, None, 4], lambda x: x is None)
    assert len(split) == 2
    assert len(split[0]) == 2
    assert len(split[1]) == 1

