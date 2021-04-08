import functools
import itertools
import os
import re
from typing import List, Iterable, Dict
import typing

from uiucprescon.packager.common import Metadata, InstantiationTypes

from .abs_package_builder import AbsPackageBuilder
from .collection_builder import AbsCollectionBuilder
from .collection import \
    Instantiation, \
    Item, \
    Package, \
    PackageObject, \
    Batch


__all__ = ['ArchivalNonEAS']


class ArchivalNonEAS(AbsPackageBuilder):
    """Archival collections."""

    def locate_packages(self, path: str) -> typing.Iterator[Package]:
        package_builder = ArchivalNonEASBuilder()
        yield from package_builder.build_batch(path)

    def transform(self, package: Package, dest: str) -> None:
        raise NotImplementedError("ArchivalNonEAS can only be read")


class ArchivalNonEASBuilder(AbsCollectionBuilder):
    grouper_regex = re.compile(
        r"^(?P<batch>[0-9]+)"
        r"_"
        r"(?P<group>[0-9]+)"
        r"-"
        r"(?P<part>[0-9]*)"
        r"(?P<extension>\.tif?)$"
    )

    @staticmethod
    def filter_only_access_files(item: "os.DirEntry[str]") -> bool:
        if not item.is_file():
            return False
        _, extension = os.path.splitext(item.name)
        if extension.lower() != ".tif":
            return False
        return True

    def group_packages(
            self,
            files: Iterable["os.DirEntry[str]"]
    ) -> Dict[str, List["os.DirEntry[str]"]]:

        def key(item: "os.DirEntry[str]") -> str:
            regex_match = self.grouper_regex.match(item.name)
            if regex_match is not None:
                return regex_match.groupdict()['group']
            return ""

        return {
            group_key: [
                file for file in files
            ] for (group_key, files) in itertools.groupby(files, key=key)
        }

    def build_batch(self, root: str) -> Batch:
        new_batch = Batch(root)
        self.build_package(parent=new_batch, path=root)

        return new_batch.children[0]

    def build_instance(self, parent: Item, path: str, filename: str, *args,
                       **kwargs) -> None:
        if "access" in path:
            new_instance = Instantiation(
                category=InstantiationTypes.ACCESS,
                parent=parent
            )

        elif "preservation" in path:
            new_instance = Instantiation(
                category=InstantiationTypes.PRESERVATION,
                parent=parent
            )
        else:
            raise ValueError(f"Expecting 'access' or 'preservation' in {path}")
        new_instance.component_metadata[Metadata.PATH] = os.path.dirname(path)
        new_instance._files.append(filename)

    def filter_file_is_item_of(self,
                               item: "os.DirEntry[str]",
                               group_id: str) -> bool:

        if not item.is_file():
            return False
        matches = self.grouper_regex.match(item.name)
        if matches is None:
            return False
        return matches.groupdict().get('group') == group_id

    def build_package(self,
                      parent: Batch,
                      path: str,
                      *args,
                      **kwargs: str) -> None:

        access_path = os.path.join(path, "access")

        new_package = Package(path, parent=parent)
        grouped_access_files = self.group_packages(
            filter(
                self.filter_only_access_files,
                os.scandir(access_path)
            )
        )
        for group_name in grouped_access_files.keys():
            self.build_object(parent=new_package,
                              path=path,
                              group_name=group_name)

    def build_object(self,
                     parent: Package,
                     path: str,
                     *args,
                     **kwargs: str) -> None:

        new_object = PackageObject(parent=parent)
        new_object.component_metadata[Metadata.ID] = kwargs['group_name']
        access_dir = os.path.join(path, "access")
        for item_file in filter(
                functools.partial(
                    self.filter_file_is_item_of,
                    group_id=kwargs['group_name']
                ),
                os.scandir(access_dir)
        ):
            match_result = self.grouper_regex.match(item_file.name)
            if match_result is None:
                raise AttributeError("Unable to match file structure")

            part = match_result.groupdict()['part']
            self.build_item(parent=new_object, item_id=part, path=path)

    def build_item(self,
                   parent: PackageObject,
                   item_id: str,
                   path: str) -> None:

        new_item = Item(parent=parent)
        new_item.component_metadata[Metadata.ITEM_NAME] = item_id
        new_item.component_metadata[Metadata.PATH] = path
        access_path = os.path.join(path, "access")
        preservation_path = os.path.join(path, "preservation")
        for item in itertools.chain.from_iterable([
            os.scandir(access_path),
            os.scandir(preservation_path)
        ]):
            match_result = self.grouper_regex.match(
                typing.cast(str, item.name)
            )
            if match_result is None:
                raise AttributeError("Unable to match file structure")

            file_naming_parts = match_result.groupdict()

            if file_naming_parts['group'] != parent.metadata[Metadata.ID]:
                continue

            if file_naming_parts['part'] != item_id:
                continue

            self.build_instance(new_item,
                                path=typing.cast(str, item.path),
                                filename=typing.cast(str, item.name)
                                )
