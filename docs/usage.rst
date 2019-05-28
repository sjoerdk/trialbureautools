.. _usage:

=====
Usage
=====

Basics
======

The trial bureau tools are accessed from command line. On windows you can start a command line
(also called 'terminal' or 'shell') in the following way:

* Press ``windows-key + r``

* type 'cmd' and press ``enter``


After that, typing ``'tbt' + enter`` will show the different commands available trial bureau tools.

You can add '--help' to any command to see more info on using it. For example ``tbt sort --help``


DICOM sorter
============
To sort all DICOM files in directory ``job1`` using the ``nucmed`` pattern:

.. code-block:: console

    $ tbt sorter sort job1 nucmed



To see what the 'nucmed' pattern is exactly:

.. code-block:: console

    $ tbt sorter pattern list



By default, sorting ``/folder1`` will write sorted output to ``/folder1_sorted``. You can also set the output
folder manually:

.. code-block:: console

    $ tbt sorter sort job1 nucmed --output_folder C:/temp/myfolder


DICOM path patterns
===================
Typing ``tbt sorter pattern list`` will by default show the following:

.. code-block:: console

    $ tbt sorter pattern list
    > idis: (0010,0020)/(0008,1030)-(0008,0050)/(0008,103e)-(0008,0060)-(0020,0011)/(count:SOPInstanceUID)
    > nucmed: (0010,0020)/(0008,1030)-(0008,0050)/(0008,0020)/(0008,103e)-(0008,0060)-(0020,0011)/(count:SOPInstanceUID)


These are the DICOM path patterns. These are text strings consisting of any combination of the following elements:

=================    ===========================================  ======================================
Element              Examples                                     Description
=================    ===========================================  ======================================
Text                 ``Folder`` ``file-`` ``/tmp``. ``.dcm``      Just any free text, inc. slash and -
Dicom Tag Code       ``(0010,0020)`` ``(0008,103e)``              A dicom tag with colons around it
Dicom Tag Name       ``(PatientID)`` ``(SopInstanceUID)``         A dicom tag name
count: marker        ``(count:PatientID)`` ``(count:0008,103e)``  Will number the given tag
=================    ===========================================  ======================================

To see a list of available Dicom tag codes and names, use ``tbt sorter pattern list_dicomtags``

Dicom Pattern resolution
------------------------
For each DICOM file a new path will be created by reading its values and filling in the pattern.
For example, for a file with PatientID '1234' and SopInstanceUID '1.1.1':

=============================================    =============================================
Pattern                                          Result (1 file)
=============================================    =============================================
``/folder1/(PatientID)/(SopInstanceUID).dcm``    ``/folder1/1234/1.1.1.dcm``
=============================================    =============================================

Counting
--------
Counting can be useful to make paths shorter. By adding ``count:`` to an element, the sorter will
number each unique value. For example, for three files with the same PatientID but separate SopInstanceUIDs:

==============================================    =============================================
Pattern without :count                            Result (3 files)
==============================================    =============================================
``/folder1/(PatientID)/(SopInstanceUID).dcm``     ``/folder1/1234/1.3451.35356.4234.1.dcm``
|                                                 ``/folder1/1234/1.3451.35356.4234.2.dcm``
|                                                 ``/folder1/1234/1.3451.35356.4234.3.dcm``
==============================================    =============================================


=======================================================    =============================================
Pattern with :count                                        Result (3 files)
=======================================================    =============================================
``/folder1/(PatientID)/file(count:SopInstanceUID).dcm``    ``/folder1/1234/file0.dcm``
|                                                          ``/folder1/1234/file1.dcm``
|                                                          ``/folder1/1234/file2.dcm``
=======================================================    =============================================


Adding custom patterns
----------------------
To add a new pattern ``/folder1/(PatientID)/file(count:SopInstanceUID).dcm`` named ``test``:

.. code-block:: console

    $ tbt sorter pattern add test /folder1/(PatientID)/file(count:SopInstanceUID).dcm


To remove this pattern again:

.. code-block:: console

    $ tbt sorter pattern remove test

