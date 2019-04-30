#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pathlib import Path

import pytest
from tests import RESOURCE_PATH
from trialbureautools.dicomsort import (
    PathMapper,
    PathGenerator,
    DicomPathPattern,
    DicomPathPatternException,
)
from trialbureautools.parser import FolderSeparator, DicomTag, StringLiteral


@pytest.fixture
def some_dicom_files():
    dicom_dir = RESOURCE_PATH / "adicomdir"
    files = [x for x in dicom_dir.glob("**/*") if x.is_file()]
    return files


def test_dicom_sort(some_dicom_files):
    """ Check whether files are mapped to expected new locations"""

    # map all files to a single string, bit silly, but possible
    sorter = PathMapper(PathGenerator(DicomPathPattern("kees")))
    mapped = sorter.map(some_dicom_files)
    assert set(mapped.values()) == {"kees"}

    sorter = PathMapper(
        PathGenerator(DicomPathPattern("(PatientID)/thing/(SOPInstanceUID)"))
    )
    mapped = sorter.map(some_dicom_files)
    assert set(mapped.values()) == {
        "300034001/thing/1.3.6.1.4.1.25403.345051766658.5228.20160418093524.118",
        "282497552115908864921858108877181315664/thing/1.3.6.1.4.1.14519.5.2.1.9999.9999.100715157022399267532658753333",
    }


@pytest.mark.parametrize(
    "pattern",
    [
        ("(StudyInstanceUID)(Somethingunparsable)"),
        ("(StudyInstanceUID)("),
        ("(StudyUID))"),
        ("("),
        ("(()"),
        ("(1045)"),
        ("(x1045001)"),
    ],
)
def test_dicom_path_parse_exceptions(pattern):
    """Patterns that should not be accepted"""
    with pytest.raises(DicomPathPatternException):
        _ = DicomPathPattern(pattern)


@pytest.mark.parametrize(
    "pattern",
    [
        ("(StudyInstanceUID)"),
        ("(0010,0020)/(0008,1030)-(0008,0050)/(0008,103e)-(0008,0060)-(0020,0011)"),
        ("(PatientID)/(0008,1030)/"),
        ("just_some_path/WITH/capitals/12345"),
    ],
)
def test_dicom_path_parse(pattern):
    """Patterns that should be accepted and not raise exceptions"""

    _ = DicomPathPattern(pattern)


def test_dicom_path_parse_detail():
    """Parse a long pattern and check exactly how it is parsed"""

    pattern = DicomPathPattern(
        "(0010,0020)/(0008,1030)-(0008,0050)/(0008,103e)-(0008,0060)-(0020,0011)"
    )
    assert len(pattern.elements) == 11
    assert len([x for x in pattern.elements if type(x) == FolderSeparator]) == 2
    assert len([x for x in pattern.elements if type(x) == DicomTag]) == 6
    assert len([x for x in pattern.elements if type(x) == StringLiteral]) == 3
