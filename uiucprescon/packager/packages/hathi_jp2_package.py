"""Packaged files for submitting to HathiTrust with JPEG 2000 files."""

# pylint: disable=unsubscriptable-object
import abc
import itertools
import logging
import os
import pathlib
import typing
from typing import Iterator
from uiucprescon.packager.packages.collection import \
    Package, Item, Instantiation, AbsPackageComponent, PackageObject
from uiucprescon import packager
from uiucprescon.packager.common import \
    Metadata, \
    PackageTypes, \
    InstantiationTypes
from .abs_package_builder import AbsPackageBuilder
from .collection_builder import AbsCollectionBuilder


__all__ = ['HathiJp2']


class AbsItemTransformStrategy(abc.ABC):  # pylint: disable=R0903
    """Abstract class for transforming Item objects."""

    def __init__(self, logger: typing.Optional[logging.Logger] = None) -> None:
        self.logger = logger or logging.getLogger(__name__)
        super().__init__()

    @abc.abstractmethod
    def transform_access_file(
            self,
            item: Item,
            dest: str
    ) -> None:
        """Transform the access files of an item."""


class CopyStrategy(AbsItemTransformStrategy):
    """Copy files without modifying them."""

    def __init__(self, logger: typing.Optional[logging.Logger] = None) -> None:
        super().__init__(logger)
        self.transformer = packager.transformations.Transformers(
            strategy=packager.transformations.CopyFile(),
            logger=logger
        )

    def transform_access_file(self, item: Item, dest: str) -> None:
        item_name = typing.cast(str, item.metadata[Metadata.ITEM_NAME])
        object_name = typing.cast(str, item.metadata[Metadata.ID])
        new_item_path = os.path.join(dest, object_name)
        inst = item.instantiations[InstantiationTypes.ACCESS]

        files = list(inst.get_files())
        if len(files) != 1:
            raise AssertionError(
                f"Expected 1 file, found {len(files)}")

        for file_ in files:
            file_name = pathlib.Path(file_).name
            _, ext = os.path.splitext(file_name)

            new_file_name = str(int(item_name)).zfill(8) + ext
            new_file_path = os.path.join(new_item_path, new_file_name)
            self.transform_file(file_, new_file_path)

    def transform_file(self, source: str, destination: str) -> None:
        """Copy file from source to destination."""
        self.transformer.transform(
            source=source,
            destination=destination)


class ConvertStrategy(AbsItemTransformStrategy):
    """Convert file from one format into another.

    This is most likely going to be a jp2000 file format.
    """

    def __init__(
            self,
            instance_source: InstantiationTypes,
            logger: typing.Optional[logging.Logger] = None
    ) -> None:
        super().__init__(logger)
        self._instance_type = instance_source

    def transform_access_file(self, item: Item, dest: str) -> None:

        inst = item.instantiations[self._instance_type]
        files = list(inst.get_files())
        if len(files) != 1:
            raise AssertionError(
                "transform_access_file only works with an instance that has "
                "a single file"
            )
        source = files[0]
        new_file_path = self.get_output_name(item, dest)
        self.convert(source, new_file_path)

    @staticmethod
    def get_output_name(reference_item: Item, dest: str) -> str:
        """Derive output file name and path from reference item."""
        item_name = typing.cast(
            str,
            reference_item.metadata[Metadata.ITEM_NAME]
        )

        object_name = typing.cast(
            str,
            reference_item.metadata[Metadata.ID]
        )

        new_item_path = os.path.join(dest, object_name)

        new_file_name = str(int(item_name)).zfill(8) + ".jp2"
        return os.path.join(new_item_path, new_file_name)

    def convert(self, source: str, destination: str) -> None:
        """Generate a new image file into the destination path."""
        file_transformer = packager.transformations.Transformers(
            strategy=packager.transformations.ConvertJp2Hathi(),
            logger=self.logger
        )
        if pathlib.Path(destination).parent.exists() is False:
            pathlib.Path(destination).parent.mkdir()
        file_transformer.transform(source, destination)


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
            transformation_strategy = self._get_item_transformer_strategy(item)
            self.transform_one_item(item, dest, transformation_strategy)

    def transform_one_item(
            self,
            item: Item,
            dest: str,
            transformation_strategy: AbsItemTransformStrategy = None,
    ) -> None:
        """Transform a single item."""
        strategy = \
            transformation_strategy or \
            self._get_item_transformer_strategy(item)

        strategy.transform_access_file(item, dest)

    @staticmethod
    def _get_item_transformer_strategy(
            item: Item
    ) -> AbsItemTransformStrategy:

        if InstantiationTypes.ACCESS in item.instantiations:
            access = item.instantiations[InstantiationTypes.ACCESS]
            if any(f.lower().endswith(".tif") for f in access.get_files()):
                return ConvertStrategy(InstantiationTypes.ACCESS)
            return CopyStrategy()
        return ConvertStrategy(InstantiationTypes.PRESERVATION)


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
            path: str,
            filename: str,
            *args,
            **kwargs
    ) -> None:
        """Build Instance."""
        sidecar_files: typing.List[os.DirEntry[str]]
        main_files: typing.List[os.DirEntry[str]]
        main_files, sidecar_files = self._locate_instance_files(filename, path)

        new_instantiation = Instantiation(category=InstantiationTypes.ACCESS,
                                          parent=parent,
                                          files=main_files
                                          )

        for file_ in sidecar_files:
            new_instantiation.sidecar_files.append(file_.path)

    def _locate_instance_files(self, filename, path):
        matching_files = \
            filter(lambda x, file_name=filename:
                   self.filter_same_name_files(x, file_name), os.scandir(path))
        sidecar_files: typing.List[os.DirEntry[str]] = []
        main_files: typing.List[os.DirEntry[str]] = []
        key: str
        value: typing.Iterator[os.DirEntry[str]]
        file_: os.DirEntry[str]

        for key, value in itertools.groupby(
                matching_files,
                key=self._organize_files
        ):
            for file_ in value:
                if key == "sidecar":
                    sidecar_files.append(file_)
                elif key == "main_files":
                    main_files.append(file_)
        return main_files, sidecar_files
