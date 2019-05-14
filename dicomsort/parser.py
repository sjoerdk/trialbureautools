"""Parser for path patterns. Parses patterns like "/tmp/(PatientID)/file(count:SopClassInstanceUID)" into relevant
pieces.

"""

import os
import re

from lark import Lark, Transformer
from lark.exceptions import LarkError
from pydicom.datadict import tag_for_keyword, keyword_dict
from pydicom.tag import Tag


class DicomPathPatternParser:
    def __init__(self):
        self.parser = Lark(
            r"""                
                            dicom_path_pattern: root_slash? element+ 
                            element: dicom_element|string_literal|folder_separator
                            string_literal: STRING_LITERAL                       
                            dicom_element: "(" count_flag? (dicom_element_tag_name | dicom_element_tag_code) ")"
                            dicom_element_tag_name: LETTER+
                            dicom_element_tag_code: HEXDIGIT~4 COMMA HEXDIGIT~4
                            root_slash.2:"/"
                            folder_separator:"/"|"\\"
                            count_flag: "count:"
                            STRING_LITERAL: (LETTER|"_"|"-"|"+"|"."|DIGIT)+
                            COMMA: ","
                            
                            
                            %import common.LETTER -> LETTER 
                            %import common.DIGIT -> DIGIT 
                             %import common.HEXDIGIT -> HEXDIGIT                                                                   
                            """,
            parser="earley",
            start="dicom_path_pattern",
        )

    def parse(self, dicom_path_string):
        """

        Parameters
        ----------
        dicom_path_string: str
            parse this string

        Returns
        -------
        List[DicomPathElement]:
            List with different DicomPathElements for each string literal, dicom tag or dicom tag name

        Raises
        ------
        DicomPatternException:
            if anything goes wrong during parsing

        """
        try:
            parsed = self.parser.parse(dicom_path_string)
        except LarkError as e:
            raise DicomPathParseException(e)

        transformed = DicomPathPatternTransformer().transform(parsed)

        # check whether all dicom tag names are valid
        tag_names = [x for x in transformed if type(x) == DicomTagName]
        for tag_name in tag_names:
            if not tag_name.is_valid():
                raise DicomPathParseException(
                    f"Dicom tag name '{tag_name}' not recognized. What is this tag?"
                )

        return transformed

    @staticmethod
    def valid_dicom_tag_names():
        """All tag_name - tag pairs that are accepted by this parser. Sorted by tagfrom pydicom.tag import Tag

        Returns
        -------
        List[(str,str)]:
            List of tag name, tag pairs that can be used in the paths for this parser
            example: ('PatientID', '(0010,0020)')

        """

        return [(x, str(Tag(y)).replace(" ", "")) for x, y in keyword_dict.items()]


class DicomPathPatternTransformer(Transformer):
    """Transforms rules like
    '(PatientID)/(0008,1030)-(0008,0050)/a_folder/'
     into a manageable datastructure

     """

    def transform(self, tree):
        """Transform a CTP script parsed with ctp_script_parser into a useful datastructure

        Parameters
        ----------
        tree:
            output of Lark().parse()

        Returns
        -------
        List[]

        Raises
        ------
        DicomPathParseException
            when parsing fails

        """
        try:
            return self._transform_tree(tree)
        except LarkError as e:
            DicomPathParseException(e)

    def dicom_path_pattern(self, items):
        return items

    def element(self, items):
        return items[0]

    def root_slash(self, items):
        return RootSlash()

    def string_literal(self, items):
        return StringLiteral("".join(items))

    def folder_separator(self, items):
        return FolderSeparator()

    def dicom_element(self, items):
        if 'count_flag' in items:
            tag_element = items[1]
            tag_element.count = True
        else:
            tag_element = items[0]
        return tag_element

    def count_flag(self, items):
        return "count_flag"

    def dicom_element_tag_code(self, items):
        return DicomTag("".join(items))

    def dicom_element_tag_name(self, items):
        tag_name = "".join(items)
        return DicomTagName(tag_name)


class DicomPathElement:
    def resolve(self, ds):
        """Resolve tags like 'PatientID' to actual value of patient ID in dataset

        Parameters
        ----------
        ds: pydicom Dataset

        Returns
        -------
        ResolvedPathElement

        Raises
        ------
        DicomTagResolutionException
            If anything goes wrong when resolving

        """
        raise NotImplemented()

    def is_valid(self):
        """Does this tag make sense, is it a valid DICOM tag, etc."""
        raise NotImplemented()


class StringLiteral(DicomPathElement):
    """Just a string """

    def __init__(self, content):
        self.content = content

    def __str__(self):
        return self.content

    def resolve(self, ds):
        """No resolving, just return literal string

        Parameters
        ----------
        ds: pydicom Dataset

        Returns
        -------
        ResolvedPathElement

        """
        return ResolvedPathElement(path_element=self, resolved_value=self.content)

    def is_valid(self):
        """String literal is always valid. And always literal"""
        return True


class FolderSeparator(DicomPathElement):
    """Just a string """

    def __str__(self):
        return os.sep

    def resolve(self, ds):
        """No resolving, just return literal string

        Parameters
        ----------
        ds: pydicom Dataset

        Returns
        -------
        str:
            path separator for current os

        """
        return ResolvedPathElement(path_element=self, resolved_value=os.sep)

    def is_valid(self):
        return True


class RootSlash(DicomPathElement):
    """The first slash in a unix path. Denoting this path starts at root"""

    def __str__(self):
        return os.sep

    def resolve(self, ds):
        """No resolving, just return literal string

        Parameters
        ----------
        ds: pydicom Dataset

        Returns
        -------
        str:
            path separator for current os

        """
        return ResolvedPathElement(path_element=self, resolved_value="/")

    def is_valid(self):
        return True


class VariableElement(DicomPathElement):
    """An element which can have different names according to which file you resolve it with.

    """

    def __init__(self, count=False):
        """

        Parameters
        ----------
        count: Bool, Optional
            False indicates that the string representation for this element should just be the actual value
            True indicates that each unique value should be numbered instead
            defaults to False

        Notes
        -----
        The count parameter only makes sense when this element is resolved in the context of multiple files. The
        parameter is only an indication for more higher level methods.

        Example:
        3 files with PatientID:
        file1 -> 1232353468756
        file2 -> 1232353468756
        file3 -> 8893843948798

        With count = False, resolution should yield
        file1 -> 1232353468756
        file2 -> 1232353468756
        file3 -> 8893843948798

        With count = True, resolution should yield
        file1 -> 1
        file2 -> 1
        file3 -> 2

        """
        self.count = count

    @staticmethod
    def clean_string(string_in):
        return string_in.strip().replace(" ", "_")


class DicomTag(VariableElement):
    """A dicom tag like '0010,0020'"""

    def __init__(self, tag_code, count=False):
        super(DicomTag, self).__init__(count)
        self.tag_code = tag_code

    def __str__(self):
        return self.tag_code

    def is_valid(self):
        """Tag code should be a string of form 'xxxx,xxxx' where x is a hexadecimal Assert this"""
        return re.match('[0-9a-fA-F]{4},[0-9a-fA-F]{4}', self.tag_code) is not None

    def resolve(self, ds):
        """Resolve tags like 'PatientID' to actual value of patient ID in dataset

        Parameters
        ----------
        ds: pydicom Dataset

        Returns
        -------
        str

        Raises
        ------
        DicomTagResolutionException
            If the given tag is not present in the data

        """
        if not self.is_valid():
            raise DicomTagResolutionException(f"Tag ({self.tag_code}) is not valid. Should be xxxx,xxxx ")
        try:
            tag_value = str(ds[self.tag_code[0:4], self.tag_code[5:9]].value)
            tag_value = self.clean_string(tag_value)
            return ResolvedPathElement(path_element=self, resolved_value=tag_value)
        except KeyError:
            raise DicomTagNotFoundException(f"Tag ({self.tag_code}) was not found")


class DicomTagName(VariableElement):
    """Tag name like 'PatientID' """
    def __init__(self, name, count=False):
        super(DicomTagName, self).__init__(count)
        self.name = name

    def __str__(self):
        return self.name

    def is_valid(self):
        return tag_for_keyword(self.name) is not None

    def resolve(self, ds):
        """Resolve tags like 'PatientID' to actual value of patient ID in dataset

        Parameters
        ----------
        ds: pydicom Dataset

        Returns
        -------
        str

        Raises
        ------
        DicomTagResolutionException
            If the given tag is not present in the data

        """
        if not self.is_valid():
            raise DicomTagResolutionException(f"I don't know tag ({self.name})")
        try:
            tag_value = ds[tag_for_keyword(self.name)].value
            tag_value = self.clean_string(tag_value)
            return ResolvedPathElement(path_element=self, resolved_value=tag_value)
        except KeyError:
            raise DicomTagNotFoundException(f"Tag ({self.name}) was not found")


class ResolvedPathElement:

    def __init__(self, path_element, resolved_value):
        """Resolved element, because sometimes you need to check the original path element to change the resolved value
        For instance when path_element.count =  True

        Parameters
        ----------
        path_element: DicomPathElement
            The original element
        resolved_value: str
            the value that this element was resolved to


        """
        self.path_element = path_element
        self.resolved_value = resolved_value

    def __str__(self):
        return f"{self.path_element} -> {self.resolved_value}"

    def count(self):
        """Does this path element indicate renaming by counting unique items?"""
        if hasattr(self.path_element, 'count'):
            return self.path_element.count
        else:
            return False


class DicomPathParseException(Exception):
    pass

class DicomTagResolutionException(Exception):
    pass

class DicomTagNotFoundException(DicomTagResolutionException):
    pass
