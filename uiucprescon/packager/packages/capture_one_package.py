"""Package generated from the lab using Capture One."""

# pylint: disable=unsubscriptable-object
from __future__ import annotations

import logging
import os
import re
import typing
from typing import Optional, Dict, Callable, Iterator, Iterable
from uiucprescon.packager import transformations
from uiucprescon.packager.common import \
    Metadata, PackageTypes, InstantiationTypes
from uiucprescon.packager.packages import collection_builder, collection
from .abs_package_builder import AbsPackageBuilder


class CaptureOneBuilder(collection_builder.AbsCollectionBuilder):
    """CaptureOneBuilder.

    .. versionadded:: 0.2.11
        Identifying the components of the filename can be done modified by
        adding a function to the splitter property
    """

    def __init__(self) -> None:
        """Init a new CaptureOneBuilder."""
        super().__init__()
        self.splitter: \
            Optional[Callable[[str], Optional[Dict[str, str]]]] = None

    def identify_file_name_parts(self,
                                 file_name: str) -> Optional[Dict[str, str]]:
        """Identify the components that make up the file name.

        Args:
            file_name: the name of a given file

        Returns:
            Dictionary of all the identified components in the file

        """
        if self.splitter is not None:
            # pylint: disable=not-callable
            # This is a callable via dependency injection by assigning splitter
            #   to a function.
            return self.splitter(file_name)
        return underscore_splitter(file_name)

    @classmethod
    def locate_batch_files(cls, root: str) -> Iterable["os.DirEntry[str]"]:
        """Locate tiff files found on root."""
        def filter_only_tiff(item: "os.DirEntry[str]") -> bool:
            return item.name.lower().endswith(".tif")

        for file_ in filter(
                filter_only_tiff,
                filter(
                    CaptureOneBuilder.filter_nonsystem_files_only,
                    os.scandir(root)
                )):
            yield file_

    def build_batch(self, root: str) -> collection_builder.AbsPackageComponent:
        """Build a capture one style batch object."""
        new_batch = collection.Package(root)
        new_batch.component_metadata[Metadata.PATH] = root

        files = list(self.locate_batch_files(root=root))

        files.sort(key=lambda f: f.name)

        group_ids = set()

        for file_ in files:
            try:
                file_name_parts = self.identify_file_name_parts(file_.name)
                if file_name_parts is None:
                    raise ValueError(
                        f"File {file_.name} doesn't match expected pattern"
                    )

                group_id = file_name_parts['group']
                group_ids.add(group_id)
            except ValueError as error:
                raise ValueError(
                    "Unable to split {}".format(file_.name)) from error

        for object_name in sorted(group_ids):
            new_object = collection.PackageObject(parent=new_batch)
            new_object.component_metadata[Metadata.ID] = object_name

            new_object.component_metadata[Metadata.PACKAGE_TYPE] = \
                PackageTypes.CAPTURE_ONE_SESSION
            self.build_package(new_object, root)
        return new_batch

    @classmethod
    def locate_tiff_instances(
            cls,
            path: str,
            is_it_an_instance: typing.Callable[["os.DirEntry[str]"], bool]
    ) -> Iterable[str]:
        """Locate tiff files on the path."""
        return [
            file.path
            for file in filter(
                is_it_an_instance,
                filter(cls.filter_nonsystem_files_only, os.scandir(path)),
            )
            if file.name.lower().endswith(".tif")
        ]

    def build_instance(
            self,
            parent,
            path: str,
            filename: str,
            *args,
            **kwargs
    ) -> None:
        """Build a capture one style instance object."""
        group_id = parent.metadata[Metadata.ID]

        def is_it_an_instance(item: "os.DirEntry[str]") -> bool:
            if not item.is_file():
                return False
            file_name_parts = self.identify_file_name_parts(item.name)
            if file_name_parts is None:
                raise ValueError(
                    "File does not match expected naming pattern {}".format(
                        item.path)
                )
            item_group = file_name_parts['group']
            item_inst = file_name_parts['part']
            if item_inst != filename:
                return False

            if item_group != group_id:
                return False
            return True

        files = self.locate_tiff_instances(path, is_it_an_instance)

        collection.Instantiation(
            category=InstantiationTypes.PRESERVATION,
            parent=parent,
            files=files)

    @classmethod
    def get_non_system_files(cls, path: str) -> Iterable["os.DirEntry[str]"]:
        """Locate files that aren't generated by the os."""
        return filter(cls.filter_nonsystem_files_only, os.scandir(path))

    def build_package(self, parent, path: str, *args, **kwargs) -> None:
        """Build a capture one style package object."""
        group_id = parent.metadata[Metadata.ID]
        non_system_files = self.get_non_system_files(path)

        def filter_by_group(candidate_file: "os.DirEntry[str]") -> bool:
            parts = self.identify_file_name_parts(candidate_file.name)
            return parts is not None and parts['group'] == group_id

        for file_ in filter(filter_by_group, non_system_files):
            file_name_parts = self.identify_file_name_parts(file_.name)
            if file_name_parts is None:
                raise ValueError(
                    f"File does not match expected naming pattern {file_.path}"
                )
            if file_name_parts['extension'].lower() != ".tif":
                continue
            item_part = file_name_parts['part']
            new_item = collection.Item(parent=parent)
            new_item.component_metadata[Metadata.ITEM_NAME] = item_part
            self.build_instance(new_item, path, item_part)


def underscore_splitter(file_name: str) -> Optional[Dict[str, str]]:
    """Use an underscore to split the file name into components.

    Args:
        file_name: the name of a given file

    Returns: Dictionary containing the identified components

    """
    regex_builder = GrouperRegexBuilder()
    group_regex = regex_builder.build()
    result = group_regex.match(file_name)
    if result is None or len(result.groups()) == 0:
        return None
    return result.groupdict()


def dash_splitter(file_name: str) -> Optional[Dict[str, str]]:
    """Use a dash to split the file name into components.

    Args:
        file_name: the name of a given file

    Returns: Dictionary containing the identified components

    """
    regex_builder = GrouperRegexBuilder()
    regex_builder.part_delimiter = '-'
    regex_builder.volume_delimiter = '_'
    group_regex = regex_builder.build()
    result = group_regex.match(file_name)
    if result is None or len(result.groups()) == 0:
        return None
    return result.groupdict()


class CaptureOnePackage(AbsPackageBuilder):
    """Package generated from the lab using Capture One.

    This package generator splits filename using a delimiter that defaults to
    an underscore.

    + batch folder
        - uniqueID1_00000001.tif
        - uniqueID1_00000002.tif
        - uniqueID1_00000003.tif
        - uniqueID2_00000001.tif
        - uniqueID2_00000002.tif

    .. versionchanged:: 0.2.12
       CaptureOnePackage can have files with multiple volume file names.

    """

    delimiter_splitters: Dict[str,
                              Callable[[str], Optional[Dict[str, str]]]] = {
        '_': underscore_splitter,
        '-': dash_splitter
    }

    def __init__(self, delimiter: str = "_") -> None:
        """Generate a new package factory.

        Args:
            delimiter: the character uses to separate the text of the filename
                to identify the part and group the file belongs to.

                Defaults to an underscore.
        """
        self.delimiter = delimiter
        splitter = CaptureOnePackage.delimiter_splitters.get(delimiter)
        if splitter is None:
            def splitter(filename: str) -> Optional[Dict[str, str]]:
                return delimiter_splitter(
                    file_name=filename,
                    delimiter=delimiter
                )

        self.package_builder = CaptureOneBuilder()
        self.package_builder.splitter = splitter

    def locate_packages(self, path: str) -> Iterator[collection.Package]:
        """Locate Capture One style packages."""
        yield from self.package_builder.build_batch(path)

    def transform(self, package: collection.Package, dest: str) -> None:
        """Transform package into a capture one style package."""
        logger = logging.getLogger(__name__)
        logger.setLevel(AbsPackageBuilder.log_level)

        for item in package:
            item_name = item.metadata[Metadata.ITEM_NAME]
            object_name = item.metadata[Metadata.ID]
            for inst in item:
                files = list(inst.get_files())
                if len(files) != 1:
                    raise AssertionError("More than one file found")

                for file_ in files:
                    _, ext = os.path.splitext(file_)
                    new_file_name = \
                        f"{object_name}{self.delimiter}{item_name}{ext}"

                    copy = transformations.Transformers(
                        strategy=transformations.CopyFile(),
                        logger=logger
                    )
                    new_file_path = os.path.join(dest, new_file_name)
                    copy.transform(source=file_, destination=new_file_path)


def delimiter_splitter(
        file_name: str,
        delimiter: str
) -> Optional[Dict[str, str]]:
    """Split the group and part of a given file based on character delimiter.

    Args:
        file_name: the name of a given file
        delimiter: string that splits the group from the part in the file name

    Returns: Dictionary containing the identified components
    """
    result = re.match(r'^'
                      r'(?P<group>\d*)'
                      f'[{delimiter}]'
                      r'(?P<part>[0-9]*)'
                      r'(?P<extension>\.[A-Za-z0-9]*)?'
                      r'$', file_name)
    if result is None or len(result.groups()) == 0:
        return None
    return result.groupdict()


class GrouperRegexBuilder:
    """Builder for generating regex that matches files produced in the lab.

    Attributes:
        part_delimiter:
            Character uses to split the package 'part' from the rest of the
            file name.
        volume_delimiter:
            Character uses to split the package 'volume' from the rest of the
            file name.
    """

    def __init__(self) -> None:
        """Create a new builder."""
        self.part_delimiter: str = "_"
        self.volume_delimiter: typing.Optional[str] = None

    def build(self) -> typing.Pattern[str]:
        """Generate a compiled regex object for matching file names."""
        pattern: typing.List[str] = [
            r'^',
            self.get_group_regex_section(),
            self.part_delimiter,
            r'(?P<part>[0-9]*)'
            r'(?P<extension>\.[A-Za-z0-9]*)?',
            r'$'
        ]
        return re.compile(''.join(pattern))

    def get_group_regex_section(self) -> str:
        """Generate the regex section for groups."""
        if self.volume_delimiter is None:
            return r'(?P<group>\d*)'
        if self.volume_delimiter == self.part_delimiter:
            raise ValueError(
                "Unable to generate regex where volume delimiter and part "
                "delimiter have same value."
            )
        escaped_values = [
            '[', ']', '(', ')', '{', '}', '*', '+', '?', '|', '^', '$', '.',
            ',',  '\\'
        ]
        if self.volume_delimiter in escaped_values:
            volume_delimiter = f"\\{self.volume_delimiter}"
        else:
            volume_delimiter = self.volume_delimiter
        return fr"(?P<group>([0-9]+?({volume_delimiter}[0-9]+)?))"
