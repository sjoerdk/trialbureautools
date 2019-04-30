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


