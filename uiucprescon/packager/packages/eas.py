import os
import pathlib
import re
import typing
from typing import Iterable, Iterator
from collections import defaultdict

from uiucprescon.packager import Metadata
from uiucprescon.packager.packages.abs_package_builder import AbsPackageBuilder
from uiucprescon.packager.packages.collection import Package, \
    AbsPackageComponent, Batch, PackageObject, Item, Instantiation, \
    InstantiationTypes

from uiucprescon.packager.packages.collection_builder import \
    AbsCollectionBuilder

__all__ = ['Eas']


class Eas(AbsPackageBuilder):

    def locate_packages(self, path: str) -> Iterator[Package]:
        yield from EASBuilder().build_batch(path)

    def transform(self, package: Package, dest: str) -> None:
        raise NotImplementedError("Read only")


class EASBuilder(AbsCollectionBuilder):
    grouper_regex = re.compile(
        r"^(?P<group>([0-9]+))"
        r"-"
        r"(?P<part>[0-9]*)"
        r"(?P<extension>\.tif?)$"
    )

    def build_batch(self, root: str) -> AbsPackageComponent:
        new_batch = Batch(root)
        self.build_package(parent=new_batch, path=root)
        return new_batch.children[0]

    def build_instance(self,
                       parent: Item,
                       path: str,
                       filename: str,
                       *args: None,
                       **kwargs: None) -> None:

        new_instance = Instantiation(parent=parent,
                                     category=InstantiationTypes.ACCESS)
        new_instance.component_metadata[Metadata.PATH] = path
        new_instance._files.append(filename)

    def build_package(self, parent: Batch, path: str, *args, **kwargs) -> None:
        groups = defaultdict(list)
        access_path = os.path.join(path, "access")
        if not os.path.exists(access_path):
            raise FileNotFoundError(f"No access located in {path}")

        for file in self.locate_package_files(access_path):
            match_result = EASBuilder.grouper_regex.match(file.name)
            if match_result is None:
                raise ValueError(
                    f"{file.name} does not match expected file naming pattern"
                )

            group = match_result.groupdict()
            groups[group['group']].append(file)

        new_package = Package(path, parent=parent)
        for group_name, _ in groups.items():
            self.build_object(
                parent=new_package,
                group_id=group_name,
                path=path
            )

    @staticmethod
    def is_eas_file(path: 'os.PathLike[str]') -> bool:
        path = pathlib.Path(path)
        if path.is_dir():
            return False
        return EASBuilder.grouper_regex.match(path.name) is not None

    def locate_package_files(self, path: str) -> Iterable[pathlib.Path]:
        for item in typing.cast(
                Iterable[os.DirEntry],
                filter(lambda p: self.is_eas_file(pathlib.Path(p.path)),
                       os.scandir(path))
        ):
            yield pathlib.Path(item.path)

    def build_object(self, parent: Package, group_id: str, path: str) -> None:
        new_object = PackageObject(parent=parent)
        new_object.component_metadata[Metadata.ID] = group_id
        new_object.component_metadata[Metadata.PATH] = path
        access_path = os.path.join(path, "access")
        for directory_item in filter(
                lambda item: self.is_eas_file(pathlib.Path(item.path)),
                os.scandir(access_path)
        ):
            regex_result = EASBuilder.grouper_regex.match(directory_item.name)
            if regex_result is None:
                raise ValueError("Unknown pattern")

            groups = regex_result.groupdict()
            if groups['group'] != group_id:
                continue

            new_item = Item(parent=new_object)
            new_item.component_metadata[Metadata.ITEM_NAME] = \
                regex_result['part']

            self.build_instance(
                new_item,
                path=os.path.dirname(directory_item.path),
                filename=directory_item.name
            )
