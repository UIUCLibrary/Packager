"""Archival collections."""
import abc
import functools
import itertools
import os
import pathlib
import re
from typing import List, Iterable, Dict
import typing

from uiucprescon.packager.common import Metadata, InstantiationTypes
from uiucprescon.packager.packages.collection_builder import \
    AbsCollectionBuilder
from uiucprescon.packager.packages.abs_package_builder import AbsPackageBuilder
from uiucprescon.packager.packages.collection import \
    Instantiation, \
    Item, \
    Package, \
    PackageObject, \
    Batch


__all__ = ['ArchivalNonEAS', 'CatalogedNonEAS']


class ArchivalNonEAS(AbsPackageBuilder):
    """Archival collections.

    (Batch)/
        access/
            00001_001-001.tif
            00001_001-002.tif
            00001_002-001.tif
            00001_002-002.tif
        preservation/
            00001_001-001.tif
            00001_001-002.tif
            00001_002-001.tif
            00001_002-002.tif

    .. versionchanged:: 0.2.12
        ArchivalNonEAS can have files with multiple volume file names.

    """

    def locate_packages(self, path: str) -> typing.Iterator[Package]:
        """Locate archival packages.

        Args:
            path: Path to the root of packages location

        Returns:
            Returns an iterable of package.

        """
        package_builder = ArchivalNonEASBuilder()
        yield from package_builder.build_batch(path)

    def transform(self, package: Package, dest: str) -> None:
        """There is no transformation implemented for this."""
        raise NotImplementedError("ArchivalNonEAS can only be read")


class NonEASBuilder(AbsCollectionBuilder):
    """Builder for noneas packages.

    .. versionchanged:: 0.2.13
        NonEASBuilder ignores system files such as Thumbs.db.

    """

    @property
    @abc.abstractmethod
    def grouper_regex(self) -> typing.Pattern[str]:
        """Compiled regex group."""

    def build_batch(self, root: str) -> Batch:
        new_batch = Batch(root)
        self.build_package(parent=new_batch, path=root)

        return new_batch.children[0]

    @staticmethod
    def filter_only_access_files(item: "os.DirEntry[str]") -> bool:
        """Filter item so that only an access file will return True."""
        if not item.is_file():
            return False
        _, extension = os.path.splitext(item.name)
        return extension.lower() == ".tif"

    def group_packages(
            self,
            files: Iterable["os.DirEntry[str]"]
    ) -> Dict[str, List["os.DirEntry[str]"]]:
        """Sort packages by group."""
        def key(item: "os.DirEntry[str]") -> str:
            regex_match = self.grouper_regex.match(item.name)
            if regex_match is not None:
                return regex_match.groupdict()['group']
            return ""

        return {
            group_key: list(
                file for file in files
            ) for (group_key, files) in itertools.groupby(files, key=key)
        }

    @staticmethod
    def locate_files_access(path: str) -> 'Iterable[os.DirEntry[str]]':
        """Locate access files."""
        return filter(NonEASBuilder.filter_only_access_files, os.scandir(path))

    @staticmethod
    def locate_files_preservation(
            path: str
    ) -> 'Iterable[os.DirEntry[str]]':
        """Locate preservation files."""
        return os.scandir(path)

    def build_package(self, parent: Batch, path: str, *_, **__: str) -> None:

        access_path = os.path.join(path, "access")

        new_package = Package(path, parent=parent)
        grouped_access_files = self.group_packages(
            self.locate_files_access(access_path)
        )
        for group_name in grouped_access_files.keys():
            self.build_object(parent=new_package,
                              path=path,
                              group_name=group_name)

    def build_instance(self, parent: Item, path: str, filename: str, *_,
                       **__) -> None:

        if pathlib.Path(path).parent.name == "access":
            new_instance = Instantiation(
                category=InstantiationTypes.ACCESS,
                parent=parent,
                files=[filename]
            )

        elif pathlib.Path(path).parent.name == "preservation":
            new_instance = Instantiation(
                category=InstantiationTypes.PRESERVATION,
                parent=parent,
                files=[filename]
            )
        else:
            raise ValueError(f"Expecting 'access' or 'preservation' in {path}")
        new_instance.component_metadata[Metadata.PATH] = os.path.dirname(path)

    def filter_file_is_item_of(self,
                               item: "os.DirEntry[str]",
                               group_id: str) -> bool:
        """Verify that the file belongs to a group."""
        if not item.is_file():
            return False
        matches = self.grouper_regex.match(item.name)
        if matches is None:
            return False
        return matches.groupdict().get('group') == group_id

    def build_item(self,
                   parent: PackageObject,
                   item_id: str,
                   path: str) -> None:
        """Build an item object.

        Args:
            parent:
            item_id:
            path:

        """
        new_item = Item(parent=parent)
        new_item.component_metadata[Metadata.ITEM_NAME] = item_id
        new_item.component_metadata[Metadata.PATH] = path
        access_path = os.path.join(path, "access")
        preservation_path = os.path.join(path, "preservation")
        for item in \
                filter(
                    self.filter_nonsystem_files_only,
                    itertools.chain.from_iterable(
                        [
                            self.locate_files_access(access_path),
                            self.locate_files_preservation(preservation_path)
                        ])
                ):
            match_result = self.grouper_regex.match(
                typing.cast(str, item.name)
            )
            if match_result is None:
                raise AttributeError(
                    f"{item.path} does not match expected file structure"
                )

            file_naming_parts = match_result.groupdict()

            if file_naming_parts['group'] != parent.metadata[Metadata.ID]:
                continue

            if file_naming_parts['part'] != item_id:
                continue

            self.build_instance(new_item,
                                path=typing.cast(str, item.path),
                                filename=typing.cast(str, item.name)
                                )

    def build_object(self,
                     parent: Package,
                     path: str,
                     *_,
                     **kwargs: str) -> None:
        """Build an object object.

        Args:
            parent:
            path:
            *_:
            **kwargs:

        """
        new_object = PackageObject(parent=parent)
        new_object.component_metadata[Metadata.ID] = kwargs['group_name']
        access_dir = os.path.join(path, "access")
        for item_file in filter(
                self.filter_nonsystem_files_only,
                filter(
                    functools.partial(
                        self.filter_file_is_item_of,
                        group_id=kwargs['group_name']
                    ),
                    self.locate_files_access(access_dir)
                )):

            match_result = self.grouper_regex.match(item_file.name)
            if match_result is None:
                raise AttributeError(
                    f"{item_file.path} does not match expected file structure"
                )

            part = match_result.groupdict()['part']
            self.build_item(parent=new_object, item_id=part, path=path)


class ArchivalNonEASBuilder(NonEASBuilder):
    """For building archival/ non-eas packages."""

    grouper_regex = re.compile(
        r"^(?P<group>([0-9]+_)+[0-9]+)"
        r"-"
        r"(?P<part>[0-9]*)"
        r"(?P<extension>\.tif?)$"
    )


class CatalogedNonEAS(AbsPackageBuilder):
    """Cataloged Non-EAS package.

    (Batch)/
        access/
            MMSID1-001.tif
            MMSID1-002.tif
            MMSID2-001.tif
            MMSID2-002.tif
        preservation/
            MMSID1-001.tif
            MMSID1-002.tif
            MMSID2-001.tif
            MMSID2-002.tif
    """

    def locate_packages(self, path: str) -> typing.Iterator[Package]:
        """Locate packages found at a given path."""
        package_builder = CatalogedNonEASBuilder()
        yield from package_builder.build_batch(path)

    def transform(self, package: Package, dest: str) -> None:
        """Transform a package into a the current type at given destination.

        Not Implemented!
        """
        raise NotImplementedError("read only")


class CatalogedNonEASBuilder(NonEASBuilder):
    """For building cataloged / non-eas packages.

    Examples:
        >>> CatalogedNonEASBuilder.grouper_regex.match("123-12312.tif")
        <re.Match object; span=(...), match='123-12312.tif'>

        >>> CatalogedNonEASBuilder.grouper_regex.match("1234-12312.tif")
        <re.Match object; span=(...), match='1234-12312.tif'>

        >>> CatalogedNonEASBuilder.grouper_regex.match("1234_1-00000001.tif")
        <re.Match object; span=(...), match='1234_1-00000001.tif'>

        >>> CatalogedNonEASBuilder.grouper_regex.match("spam") is None
        True

        >>> matcher = CatalogedNonEASBuilder.grouper_regex
        >>> matcher.match("1234_1-00000001.tif").groupdict()['group']
        '1234_1'
    """

    grouper_regex = re.compile(
        r"^(?P<group>([0-9])+(_[0-9]+)?)"
        r"-"
        r"(?P<part>[0-9]*)"
        r"(?P<extension>\.tif?)$"
    )
