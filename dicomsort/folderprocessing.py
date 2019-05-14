"""Classes and functions that can map all files in a folder and handle errors

Made this to separate the nitty-gritty of filesystem operations from pure-python modules
"""
from os import makedirs
from itertools import zip_longest
from pathlib import Path
from shutil import copyfile

from dicomsort.core import UserPathMapping
from dicomsort.mappers import FullPathMapper, MappingException


class FolderMapper:
    """Maps all files in folder to new locations

    """

    def __init__(self):
        pass

    def generate_mapping(self, input_folder, output_folder, pattern):
        """Does not move any files, instead just check whether there are any problems with the intended mapping
        Reads in all files in folder so might be slow

        Parameters
        ----------
        input_folder: Path
            Map each file in this folder
        output_folder: Path
            To an output path starting with this folder
        pattern: str
            Where the path within output_folder is given by this pattern

        Returns
        -------
        PathMapping
            Mapping of each input file to output file

        Raises
        ------
        FolderMapperException:
            When anything goes wrong during mapping


        """
        # check availability of output folder. Try to fail early here
        input_folder = Path(input_folder)
        output_folder = Path(output_folder)
        files = [x for x in input_folder.glob("**/*") if x.is_file()]
        mapper = FullPathMapper(pattern=pattern, root_path=output_folder, check_path_lengths=True)
        try:
            mapping = mapper.map(files)
        except MappingException as e:
            msg = f'Error trying to map: {e}'
            raise FolderMapperException(msg)

        return mapping

    def execute_mapping(self, mapping):
        """Copy each file in mapping to its mapped destination

        Parameters
        ----------
        mapping: PathMapping
            Mapping of original file paths to mapped paths


        Raises
        ------
        FolderMapperException:
            When copying fails for any file


        """
        flat = mapping.as_flat_dict()
        for source, destination in flat.items():
            try:
                makedirs(destination.parent, exist_ok=True)
                copyfile(source, destination)
            except OSError as e:
                msg = f"Error trying to copy {source} to {destination}: {e}"
                raise FolderMapperException(msg)

    def get_executions_chunks(self, mapping, number_of_chunks):
        """Split execution of this mapping into chunks. Each chunk can be executed individually
        Mapping items will be distributed over chunks as well as possible.
        If number of chunks is larger then number of mapping items, some of the returned Delayed functions will be
        empty

        Parameters
        ----------
        mapping: PathMapping
            mapping to cut into chunks
        number_of_chunks: int
            Split into this many chunks.

        Returns
        -------
        List(DelayedFunction):
            List of delayed functions, each of which does execute_mapping() on part of

        """
        # split mapping
        item_chunks = [list(mapping.items())[i::number_of_chunks] for i in range(number_of_chunks)]
        mappings = [UserPathMapping(mapping=dict(chunk)) for chunk in item_chunks]

        chunks = [DelayedFunction(function=self.execute_mapping, kwargs={'mapping': x}) for x in mappings]
        return chunks


class ProgressBar:
    """A text-based progress bar. Goes from [#     ] to [#### ] to [#######] """

    def __init__(self, steps, current_step=0):
        """

        Parameters
        ----------
        steps: int
            number of steps this bar can have.
        current_step: int
            current number of steps taken
        """
        self.steps = steps
        self.current_step = current_step

    def __str__(self):
        return "[" + ("#"*self.current_step) + (" "*(self.steps-self.current_step)) + "]"

    def step(self):
        """Increase step by 1"""
        self.current_step = min(self.steps, self.current_step + 1)

    def reset(self):
        self.current_step = 0


def grouper(n, iterable, padvalue=None):
    """grouper(3, 'abcdefg', 'x') --> ('a','b','c'), ('d','e','f'), ('g','x','x')"""

    return zip_longest(*[iter(iterable)]*n, fillvalue=padvalue)


class DelayedFunction:
    """Encapsulates a single function call with parameters. Can be called with .execute()

    """
    def __init__(self, function, args=None, kwargs=None):
        """

        Parameters
        ----------
        function: python function
            function to call
        args: List, optional
            list of arguments, defaults to empty list
        kwargs: Dict, optional
            dictionary of keyword arguments, defaults to empty dict
        """
        if not args:
            args = []
        if not kwargs:
            kwargs = {}
        self.function = function
        self.args = args
        self.kwargs = kwargs

    def execute(self):
        return self.function(*self.args, **self.kwargs)


class FolderMapperException(Exception):
    pass
