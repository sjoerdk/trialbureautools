#!/usr/bin/env python
# -*- coding: utf-8 -*-
from os import listdir
from os.path import isfile

import pydicom
import pytest
from tests import RESOURCE_PATH

from trialbureautools.parser import DicomTag, DicomTagName, StringLiteral, DicomTagResolutionException


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
    assert element.resolve(ds) == resolved


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
