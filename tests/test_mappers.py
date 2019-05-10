#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from pathlib import Path

import pytest
from tests import RESOURCE_PATH
from dicomsort.core import (
    PathGenerator,
    DicomPathPattern)
from dicomsort.mappers import StraightPathMapper, FullPathMapper, UnsafeMappingException, OverlappingFilePathException, \
    PathTooLongForWindowsException


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

    pattern = "(PatientID)/(0008,0060)-study(count:StudyDescription)/(SeriesDescription)/file(count:SOPInstanceUID)"

    mapper = FullPathMapper(pattern=pattern)
    tree = mapper.map(some_more_dicom_files)
    final = sorted(list(tree.as_flat_dict().values()))
    assert str(final[1]) == os.sep.join(["test0430", "CT-study0", "2.0", "file1"])
    assert str(final[7]) == os.sep.join(["test0430", "CT-study0", "AiCE_3.000_CE", "file05"])

    silly_mapper = FullPathMapper(pattern="(PatientID)")
    with pytest.raises(OverlappingFilePathException):
        silly_mapper.map(some_more_dicom_files)


def test_full_path_mapper_path_limit(some_more_dicom_files):
    pattern = "(PatientID)/(StudyDescription)(StudyDescription)/(SeriesDescription)/(SOPInstanceUID)(SOPInstanceUID)" \
              "(SOPInstanceUID)(SOPInstanceUID)"

    mapper = FullPathMapper(pattern=pattern)
    with pytest.raises(PathTooLongForWindowsException):
        mapper.map(some_more_dicom_files)


def test_full_path_mapper_unsafe_mapping(some_dicom_files):
    pattern = "adicomdir/folder1/file(count:SOPInstanceUID).dcm"
    mapper = FullPathMapper(pattern=pattern, root_path=RESOURCE_PATH)
    with pytest.raises(UnsafeMappingException):
        mapper.map(some_dicom_files[1:3])


def test_full_path_mapper_with_root(some_more_dicom_files):

    pattern = "(PatientID)/(0008,0060)-study(count:StudyDescription)/(SeriesDescription)/file(count:SOPInstanceUID)"
    mapper = FullPathMapper(pattern=pattern, root_path="/tmp/folder/something/")
    mapped = mapper.map(some_more_dicom_files)
    for path in mapped.as_flat_dict().values():
        assert str(path).startswith("/tmp/folder/something/")


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
