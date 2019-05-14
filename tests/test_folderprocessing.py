#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from pathlib import Path
from unittest.mock import Mock

import pytest

from dicomsort.core import UserPathMapping, DicomPathPattern
from dicomsort.mappers import (
    OverlappingFilePathException,
    PathTooLongForWindowsException,
    UnsafeMappingException,
)
from dicomsort.folderprocessing import (
    FolderMapper,
    FolderMapperException,
    DelayedFunction,
    ProgressBar)
from tests import RESOURCE_PATH


@pytest.fixture()
def folderprocessing_mock_copyfile(monkeypatch):
    """Turn off copyfile, return mock that will records calls"""
    mock_copyfile = Mock()
    mock_makedirs = Mock()
    monkeypatch.setattr("dicomsort.folderprocessing.copyfile", mock_copyfile)
    monkeypatch.setattr("dicomsort.folderprocessing.makedirs", mock_makedirs)
    return mock_copyfile


@pytest.fixture()
def folderprocessing_mock_fullpathmapper(monkeypatch):
    mock_map = Mock()
    monkeypatch.setattr("dicomsort.folderprocessing.FullPathMapper.map", mock_map)
    return mock_map


def test_folder_mapper(tmp_path, folderprocessing_mock_copyfile):
    """General tests for folderprocessor. Just run a standard program and nothing should crash"""
    output_folder = Path(tmp_path) / "folder_mapper_test"
    dicom_dir = RESOURCE_PATH / "anotherdicomdir"
    pattern = "(PatientID)/(0008,0060)-study(count:StudyDescription)/(SeriesDescription)/file(count:SOPInstanceUID)"

    mapper = FolderMapper()
    mapping = mapper.generate_mapping(
        input_folder=dicom_dir, output_folder=output_folder, pattern=pattern
    )
    mapper.execute_mapping(mapping)
    # each file should have been copied
    assert folderprocessing_mock_copyfile.call_count == len(mapping)



def test_folder_mapper_copy_errors(tmp_path, folderprocessing_mock_copyfile):
    """copying fails, should be converted to folder mapping exception"""
    mapping = UserPathMapping(
        mapping={Path("/tmp/somefile"): Path("/tmp/new/newlocation")}
    )
    mapper = FolderMapper()

    folderprocessing_mock_copyfile.side_effect = OSError("Cannot copy for some reason!")
    with pytest.raises(FolderMapperException):
        mapper.execute_mapping(mapping)


@pytest.mark.parametrize(
    "exception_raised",
    [
        OverlappingFilePathException("Overlap!"),
        PathTooLongForWindowsException("Way too long"),
        UnsafeMappingException("What were you thinking?"),
    ],
)
def test_folder_mapper_map_errors(
    tmp_path, folderprocessing_mock_fullpathmapper, exception_raised
):
    """Catch errors that might come from mapping stage. Should all be converted to folder mapping exceptions"""
    output_folder = Path(tmp_path) / "folder_mapper_test"
    dicom_dir = RESOURCE_PATH / "anotherdicomdir"
    pattern = "(PatientID)/(0008,0060)-study(count:StudyDescription)/(SeriesDescription)/file(count:SOPInstanceUID)"
    mapper = FolderMapper()

    folderprocessing_mock_fullpathmapper.side_effect = exception_raised
    with pytest.raises(FolderMapperException):
        mapper.generate_mapping(
            input_folder=dicom_dir, output_folder=output_folder, pattern=pattern
        )


def test_folder_mapper_execute_chunked(tmp_path, folderprocessing_mock_copyfile):
    """Execute a long list in chunks, so that progress can be monitored"""
    mapping = UserPathMapping(
        mapping={
            Path("sourcefile" + str(x)): Path("destfile" + str(x)) for x in range(250)
        }
    )
    mapper = FolderMapper()
    chunks = mapper.get_executions_chunks(mapping=mapping, number_of_chunks=11)
    assert len(chunks) == 11

    call_counts = [folderprocessing_mock_copyfile.call_count]
    for chunk in chunks:
        chunk.execute()
        call_counts.append(folderprocessing_mock_copyfile.call_count)

    assert call_counts == [0, 23, 46, 69, 92, 115, 138, 161, 184, 206, 228, 250]


def test_folder_mapper_execute_chunked_too_many_chunks(tmp_path, folderprocessing_mock_copyfile):
    """Test weird values for chunk"""
    mapping = UserPathMapping(
        mapping={
            Path("sourcefile" + str(x)): Path("destfile" + str(x)) for x in range(3)
        }
    )
    mapper = FolderMapper()
    chunks = mapper.get_executions_chunks(mapping=mapping, number_of_chunks=5)
    assert len(chunks) == 5

    call_counts = [folderprocessing_mock_copyfile.call_count]
    for chunk in chunks:
        chunk.execute()
        call_counts.append(folderprocessing_mock_copyfile.call_count)
    assert call_counts == [0, 1, 2, 3, 3, 3]


def test_chunked_delayed_execution():
    function1 = DelayedFunction(function="efeg".upper)
    function2 = DelayedFunction(function=range, args=[1, 3])
    function3 = DelayedFunction(
        function=DicomPathPattern, kwargs={"pattern_string": "testpath"}
    )

    assert function1.execute() == "EFEG"
    assert function2.execute() == range(1, 3)
    assert function3.execute().elements[0].content == DicomPathPattern('testpath').elements[0].content


def test_progressbar():
    bar = ProgressBar(steps=11)

    assert str(bar) == "[           ]"
    for _ in range(3):
        bar.step()
    assert str(bar) == "[###        ]"
    for _ in range(12):
        bar.step()
    assert str(bar) == "[###########]"
    bar.reset()
    assert str(bar) == "[           ]"
