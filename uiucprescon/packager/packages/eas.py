"""EAS package.

This Module contains EAS package class
"""
import os
import pathlib
import re
import typing
from typing import Iterable, Iterator
from collections import defaultdict

from uiucprescon.packager.common import Metadata
from uiucprescon.packager.packages.abs_package_builder import AbsPackageBuilder
from uiucprescon.packager.packages import collection
from uiucprescon.packager.packages.collection_builder import \
    AbsCollectionBuilder

__all__ = ['Eas']


class Eas(AbsPackageBuilder):
    """EAS package."""

    def locate_packages(self, path: str) -> Iterator[collection.Package]:
        """Locate EAS packages on a given file path.

        Args:
            path: File path to search for EAS packages

        Yields:
            EAS package

        """
        yield from EASBuilder().build_batch(path)

    def transform(self, package: collection.Package, dest: str) -> None:
        """Not Implemented."""
        raise NotImplementedError("Read only")


class EASBuilder(AbsCollectionBuilder):
    """Build EAS packages.

    Examples:
        >>> EASBuilder.grouper_regex.match("99338384012205899-00000001.tif")
        <re.Match object; span=(...), match='99338384012205899-00000001.tif'>

        >>> EASBuilder.grouper_regex.match("99338384012205899_1-00000001.tif")
        <re.Match object; span=(...), match='99338384012205899_1-00000001.tif'>

        >>> EASBuilder.grouper_regex.match("spam") is None
        True

        >>> matcher = EASBuilder.grouper_regex
        >>> matches = matcher.match("99338384012205899_1-00000001.tif")
        >>> matches.groupdict()['group']
        '99338384012205899_1'

    """

    grouper_regex = re.compile(
        r"^(?P<group>([0-9])+(_[0-9]+)?)"
        r"-"
        r"(?P<part>[0-9]*)"
        r"(?P<extension>\.tif?)$"
    )

    def build_batch(self, root: str) -> collection.AbsPackageComponent:
        new_batch = collection.Batch(root)
        self.build_package(parent=new_batch, path=root)
        return new_batch.children[0]

    def build_instance(self,
                       parent: collection.Item,
                       path: str,
                       filename: str,
                       *args: None,
                       **kwargs: None) -> None:

        new_instance = collection.Instantiation(
            parent=parent,
            category=collection.InstantiationTypes.ACCESS,
            files=[filename]
        )

        new_instance.component_metadata[Metadata.PATH] = path

    def build_package(self,
                      parent: collection.Batch,
                      path: str,
                      *args: None,
                      **kwargs: None) -> None:

        groups = defaultdict(list)
        access_path = os.path.join(path, "access")
        if not os.path.exists(access_path):
            raise FileNotFoundError(f"No access directory located in {path}")

        for file in self.locate_package_files(access_path):
            match_result = EASBuilder.grouper_regex.match(file.name)
            if match_result is None:
                raise ValueError(
                    f"{file.name} does not match expected file naming pattern"
                )

            group = match_result.groupdict()
            groups[group['group']].append(file)

        new_package = collection.Package(path, parent=parent)
        for group_name, _ in groups.items():
            self.build_object(
                parent=new_package,
                group_id=group_name,
                path=path
            )

    @staticmethod
    def is_eas_file(path: 'os.PathLike[str]') -> bool:
        """Check if inputted path belongs in an EAS package.

        Args:
            path:

        Returns:
            Returns True if file matches expected, else returns False

        """
        path = pathlib.Path(path)
        if path.is_dir():
            return False
        return EASBuilder.grouper_regex.match(path.name) is not None

    def locate_package_files(
            self,
            path: str, search_strategy=os.scandir
    ) -> Iterable[pathlib.Path]:
        """Locate any EAS files at the given path.

        Args:
            path:
            search_strategy:

        Yields:
            Any valid files at the path

        """
        for item in typing.cast(
                Iterable['os.DirEntry[str]'],
                filter(lambda p: self.is_eas_file(pathlib.Path(p.path)),
                       search_strategy(path))
        ):
            yield pathlib.Path(item.path)

    @staticmethod
    def locate_files_access(path: str) -> 'Iterable[os.DirEntry[str]]':
        """Locate access files."""
        return os.scandir(path)

    def build_object(self,
                     parent: collection.Package,
                     group_id: str,
                     path: str) -> None:
        """Build a new object.

        Args:
            parent:
            group_id:
            path:

        """
        new_object = collection.PackageObject(parent=parent)
        new_object.component_metadata[Metadata.ID] = group_id
        new_object.component_metadata[Metadata.PATH] = path
        access_path = os.path.join(path, "access")
        for directory_item in filter(
                lambda item: self.is_eas_file(pathlib.Path(item.path)),
                self.locate_files_access(access_path)
        ):
            regex_result = EASBuilder.grouper_regex.match(directory_item.name)
            if regex_result is None:
                raise ValueError("Unknown pattern")

            groups = regex_result.groupdict()
            if groups['group'] != group_id:
                continue

            new_item = collection.Item(parent=new_object)
            new_item.component_metadata[Metadata.ITEM_NAME] = \
                regex_result['part']

            self.build_instance(
                new_item,
                path=os.path.dirname(directory_item.path),
                filename=directory_item.name
            )
