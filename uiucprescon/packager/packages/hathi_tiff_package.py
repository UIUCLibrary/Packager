import logging
import os
import shutil
import typing

from uiucprescon.packager.packages import collection_builder
from uiucprescon.packager.packages.collection import Package, Metadata
from .abs_package_builder import AbsPackageBuilder


class HathiTiff(AbsPackageBuilder):
    def locate_packages(self, batch_path) -> typing.Iterator[Package]:
        for package in collection_builder.build_hathi_tiff_batch(batch_path):
            yield package

    def transform(self, package: Package, dest: str) -> None:
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)

        for item in package:
            item_name = item.metadata[Metadata.ITEM_NAME]
            object_name = item.metadata[Metadata.ID]
            new_item_path = os.path.join(dest, object_name)
            if not os.path.exists(new_item_path):
                os.makedirs(new_item_path)

            for inst in item:
                assert len(inst.files) == 1
                for file_ in inst.files:
                    _, ext = os.path.splitext(file_)

                    new_file_name = item_name + ext
                    new_file_path = os.path.join(new_item_path, new_file_name)
                    logger.info("Copying {} to {}".format(file_, new_file_path))
                    shutil.copy(file_, new_file_path)