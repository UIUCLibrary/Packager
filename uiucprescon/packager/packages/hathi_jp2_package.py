import logging
import os
import typing

from uiucprescon.packager.packages import collection_builder
from uiucprescon.packager.packages.collection import Package
from uiucprescon.packager.common import Metadata
from uiucprescon.packager import transformations
from .abs_package_builder import AbsPackageBuilder


class HathiJp2(AbsPackageBuilder):
    """Packaged files for submitting to HathiTrust with JPEG 2000 files."""
    def locate_packages(self, path) -> typing.Iterator[Package]:
        builder = collection_builder.HathiJp2Builder()
        batch = builder.build_batch(path)
        for package in batch:
            yield package

    def transform(self, package: Package, dest: str) -> None:
        logger = logging.getLogger(__name__)
        logger.setLevel(AbsPackageBuilder.log_level)

        for item in package:
            self.transform_one(item, dest, logger)

    @staticmethod
    def transform_one(item, dest, logger=None):
        item_name = item.metadata[Metadata.ITEM_NAME]
        object_name = item.metadata[Metadata.ID]
        new_item_path = os.path.join(dest, object_name)

        if not os.path.exists(new_item_path):
            os.makedirs(new_item_path)

        for inst in item:
            if len(inst.files) != 1:
                raise AssertionError(
                    f"Expected 1 file, found {len(inst.files)}")

            for file_ in inst.files:
                _, ext = os.path.splitext(file_)

                new_file_name = item_name + ext
                new_file_path = os.path.join(new_item_path, new_file_name)

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

                file_transformer.transform(source=file_,
                                           destination=new_file_path)
