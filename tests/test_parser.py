#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pydicom
import pytest
from tests import RESOURCE_PATH
from dicomsort.core import DicomPathPatternException, DicomPathPattern

from dicomsort.parser import DicomTag, DicomTagName, StringLiteral, DicomTagResolutionException, FolderSeparator


@pytest.fixture
def some_dicom_files():
    dicom_dir = RESOURCE_PATH / "adicomdir"
    files = [x for x in dicom_dir.glob("**/*") if x.is_file()]
    return files


@pytest.mark.parametrize('element, resolved',
                         [(DicomTag("0010,0020"), '300034001'),
                          (DicomTag("0008,0030"), '081625.254000'),
                          (DicomTagName("PatientID"), '300034001'),
                          (StringLiteral("test/something/"), "test/something/"),
                          (StringLiteral("kees"), "kees")])
def test_path_element_resolution(some_dicom_files, element, resolved):
    """Items that should resolve without problems"""

    ds = pydicom.dcmread(str(some_dicom_files[0]))
    assert element.resolve(ds).resolved_value == resolved


@pytest.mark.parametrize('element',
                         [(DicomTagName("StudyDescription")),
                          (DicomTag("0008,1030")),
                          (DicomTagName("UnknownTag")),
                          (DicomTag("0349"))
                          ])
def test_path_element_resolution_errors(some_dicom_files, element):
    """Items that should yield errors, either because the given tag cannot be found in the file, or because the tag
       itself is malformed or unknown
       """
    ds = pydicom.dcmread(str(some_dicom_files[0]))
    with pytest.raises(DicomTagResolutionException):
        element.resolve(ds)


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
        ("just_some_path/WITH/capitals/(count:SOPInstanceUID).dcm"),
    ],
)
def test_dicom_path_parse(pattern):
    """Patterns that should be accepted and not raise exceptions"""

    pattern = DicomPathPattern(pattern)
    for element in pattern.elements:
        assert element.is_valid()


def test_dicom_path_parse_detail():
    """Parse a long pattern and check exactly how it is parsed"""

    pattern = DicomPathPattern(
        "(0010,0020)/(0008,1030)-(0008,0050)/(0008,103e)-(0008,0060)-(0020,0011)"
    )
    assert len(pattern.elements) == 11
    assert len([x for x in pattern.elements if type(x) == FolderSeparator]) == 2
    assert len([x for x in pattern.elements if type(x) == DicomTag]) == 6
    assert len([x for x in pattern.elements if type(x) == StringLiteral]) == 3


def test_dicom_path_parse_detail():
    """Parse a long pattern and check exactly how it is parsed"""

    pattern = DicomPathPattern(
        "(count:PatientID)/(count:0008,1030)-(0008,0050)/(0008,103e)-(0008,0060)-(0020,0011)"
    )
    assert len(pattern.elements) == 11
    assert pattern.elements[0].count is True
    assert pattern.elements[2].count is True
    assert pattern.elements[4].count is False
