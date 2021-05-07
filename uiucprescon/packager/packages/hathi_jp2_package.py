"""Packaged files for submitting to HathiTrust with JPEG 2000 files."""

# pylint: disable=unsubscriptable-object
import logging
import os
import pathlib
from typing import Optional, Iterator
from uiucprescon.packager.packages import collection_builder
from uiucprescon.packager.packages.collection import Package
from uiucprescon.packager.common import Metadata
from uiucprescon.packager import transformations
from .abs_package_builder import AbsPackageBuilder


class HathiJp2(AbsPackageBuilder):
    """Packaged files for submitting to HathiTrust with JPEG 2000 files."""

    def locate_packages(self, path: str) -> Iterator[Package]:
        """Locate Hathi jp2 packages on a given file path.

        Args:
            path: File path to search for Hathi jp2 packages

        Yields:
            Hathi Jpeg2000 packages

        """
        builder = collection_builder.HathiJp2Builder()
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

        for item in package:
            self.transform_one(item, dest, logger)

    @staticmethod
    def transform_one(
            item,
            dest: str,
            logger: Optional[logging.Logger] = None
    ) -> None:
        """Transform a single item one.

        Args:
            item:
            dest:
            logger:

        """
        item_name = item.metadata[Metadata.ITEM_NAME]
        object_name = item.metadata[Metadata.ID]
        new_item_path = os.path.join(dest, object_name)

        if not os.path.exists(new_item_path):
            os.makedirs(new_item_path)

        for inst in item:
            files = list(inst.get_files())
            if len(files) != 1:
                raise AssertionError(
                    f"Expected 1 file, found {len(files)}")

            for file_ in files:
                file_ = pathlib.Path(file_).name
                _, ext = os.path.splitext(file_)

                if ext.lower() == ".jp2":

                    # If the item is already a jp2 then copy
                    file_transformer = transformations.Transformers(
                        strategy=transformations.CopyFile(),
                        logger=logger
                    )
                else:
                    # If it's not the same extension, convert it to jp2
                    file_transformer = transformations.Transformers(
                        strategy=transformations.ConvertJp2Hathi(),
                        logger=logger
                    )
                new_file_name = str(int(item_name)).zfill(8) + ".jp2"
                new_file_path = os.path.join(new_item_path, new_file_name)

                file_transformer.transform(
                    source=os.path.join(inst.metadata[Metadata.PATH], file_),
                    destination=new_file_path)
