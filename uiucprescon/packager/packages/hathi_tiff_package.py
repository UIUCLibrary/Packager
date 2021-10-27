"""Packaged files for submitting to HathiTrust containing only Tiff files."""

import logging
import os
import pathlib
from typing import Iterator
import typing
from uiucprescon.packager.packages import collection_builder
from uiucprescon.packager.packages.collection import Package, Item, Instantiation
from uiucprescon.packager import transformations
from uiucprescon.packager.common import Metadata
from .abs_package_builder import AbsPackageBuilder


class HathiTiff(AbsPackageBuilder):
    """Packaged files for submitting to HathiTrust containing Tiff files."""

    def locate_packages(self, path: str) -> Iterator[Package]:
        """Locate Hathi tiff packages on a given file path.

        Args:
            path: File path to search for Hathi tiff packages

        Yields:
            Hathi Tiff packages

        """
        builder = collection_builder.HathiTiffBuilder()
        yield from builder.build_batch(path)

    def transform(self, package: Package, dest: str) -> None:
        """Transform package into a Hathi Tiff package.

        Args:
            package: Source package to transform
            dest: File path to save the transformed package

        """
        logger = logging.getLogger(__name__)
        logger.setLevel(AbsPackageBuilder.log_level)
        item: Item
        for item in package:
            item_name = typing.cast(str, item.metadata[Metadata.ITEM_NAME])
            object_name = typing.cast(str, item.metadata[Metadata.ID])
            new_item_path = os.path.join(dest, object_name)
            if not os.path.exists(new_item_path):
                os.makedirs(new_item_path)

            inst: Instantiation
            for inst in item:
                files: typing.List[str] = list(inst.get_files())
                if len(files) != 1:
                    raise AssertionError(
                        f"Expected 1 file, found {len(files)}")
                for file_ in files:

                    _, ext = os.path.splitext(pathlib.Path(file_).name)

                    new_file_name = f"{item_name}{ext}"
                    new_file_path = os.path.join(new_item_path, new_file_name)
                    self.copy(file_, destination=new_file_path, logger=logger)

    @staticmethod
    def copy(source: str,
             destination: str,
             logger: logging.Logger = None) -> None:
        """Copy file without modifications."""
        logger = logger or logging.getLogger(__name__)

        copy = transformations.Transformers(
            strategy=transformations.CopyFile(),
            logger=logger
        )

        copy.transform(source=source, destination=destination)
