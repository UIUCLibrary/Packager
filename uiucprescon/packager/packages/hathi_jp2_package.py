"""Packaged files for submitting to HathiTrust with JPEG 2000 files."""

# pylint: disable=unsubscriptable-object
import itertools
import logging
import os
import pathlib
import typing
from typing import Optional, Iterator
from uiucprescon.packager.packages.collection import \
    Package, Item, Instantiation, AbsPackageComponent, PackageObject
from uiucprescon import packager
from uiucprescon.packager.common import \
    Metadata, \
    PackageTypes, \
    InstantiationTypes
from .abs_package_builder import AbsPackageBuilder
from .collection_builder import AbsCollectionBuilder


class HathiJp2(AbsPackageBuilder):
    """Packaged files for submitting to HathiTrust with JPEG 2000 files."""

    def locate_packages(self, path: str) -> Iterator[Package]:
        """Locate Hathi jp2 packages on a given file path.

        Args:
            path: File path to search for Hathi jp2 packages

        Yields:
            Hathi Jpeg2000 packages

        """
        builder = HathiJp2Builder()
        batch = builder.build_batch(path)
        yield from batch

    def transform(self, package: Package, dest: str) -> None:
        """Transform package into a Hathi jp2k package.

        Args:
            package: Source package to transform
            dest: File path to save the transformed package

        """
        logger = logging.getLogger(__name__)
        logger.setLevel(AbsPackageBuilder.log_level)
        item: Item
        for item in package:
            self.transform_one(item, dest, logger)

    @staticmethod
    def transform_one(
            item: Item,
            dest: str,
            logger: Optional[logging.Logger] = None
    ) -> None:
        """Transform a single item one.

        Args:
            item:
            dest:
            logger:

        """
        item_name = typing.cast(str, item.metadata[Metadata.ITEM_NAME])
        object_name = typing.cast(str, item.metadata[Metadata.ID])
        new_item_path = os.path.join(dest, object_name)

        if not os.path.exists(new_item_path):
            os.makedirs(new_item_path)
        inst: Instantiation
        for inst in item:
            files = list(inst.get_files())
            if len(files) != 1:
                raise AssertionError(
                    f"Expected 1 file, found {len(files)}")

            file_: str
            for file_ in files:
                file_ = pathlib.Path(file_).name
                _, ext = os.path.splitext(file_)

                if ext.lower() == ".jp2":

                    # If the item is already a jp2 then copy
                    file_transformer = packager.transformations.Transformers(
                        strategy=packager.transformations.CopyFile(),
                        logger=logger
                    )
                else:
                    # If it's not the same extension, convert it to jp2
                    file_transformer = packager.transformations.Transformers(
                        strategy=packager.transformations.ConvertJp2Hathi(),
                        logger=logger
                    )
                new_file_name = str(int(item_name)).zfill(8) + ".jp2"
                new_file_path = os.path.join(new_item_path, new_file_name)

                file_transformer.transform(
                    source=os.path.join(
                        typing.cast(str, inst.metadata[Metadata.PATH]),
                        file_
                    ),
                    destination=new_file_path)


class HathiJp2Builder(AbsCollectionBuilder):
    """HathiJp2Builder."""

    def build_batch(self, root: str) -> AbsPackageComponent:
        """Build batch."""
        new_batch = Package(root)
        new_batch.component_metadata[Metadata.PATH] = root

        for dir_ in filter(lambda i: i.is_dir(), os.scandir(root)):
            new_object = PackageObject(parent=new_batch)
            new_object.component_metadata[Metadata.ID] = dir_.name
            new_object.component_metadata[Metadata.PATH] = dir_.path

            new_object.component_metadata[Metadata.PACKAGE_TYPE] = \
                PackageTypes.HATHI_TRUST_JP2_SUBMISSION

            self.build_package(new_object, path=dir_.path)

        return new_batch

    @staticmethod
    def filter_tiff_files(item: 'os.DirEntry[str]') -> bool:
        """Identify if file given is a tiff file."""
        if not item.is_file():
            return False

        ext = os.path.splitext(item.name)[1]
        return ext.lower() == ".jp2"

    def build_package(self, parent, path: str, *args, **kwargs) -> None:
        """Build package."""
        for file_ in filter(self.filter_tiff_files, os.scandir(path)):
            new_item = Item(parent=parent)
            item_part, _ = os.path.splitext(file_.name)
            new_item.component_metadata[Metadata.ITEM_NAME] = item_part
            self.build_instance(new_item, path=path, filename=item_part)

    @staticmethod
    def _organize_files(item: 'os.DirEntry[str]') -> str:
        ext = os.path.splitext(item.name)[1]
        if ext.lower() == ".jp2":
            return "main_files"
        return "sidecar"

    def build_instance(
            self,
            parent,
            path,
            filename,
            *args,
            **kwargs
    ):
        """Build Instance."""
        matching_files = \
            filter(lambda x, file_name=filename:
                   self.filter_same_name_files(x, file_name), os.scandir(path))

        sidecar_files = []

        main_files = []
        for key, value in itertools.groupby(
                matching_files,
                key=self._organize_files
        ):
            for file_ in value:
                if key == "sidecar":
                    sidecar_files.append(file_)
                elif key == "main_files":
                    main_files.append(file_)

        new_instantiation = Instantiation(category=InstantiationTypes.ACCESS,
                                          parent=parent,
                                          files=main_files
                                          )

        for file_ in sidecar_files:
            new_instantiation.sidecar_files.append(file_.path)
