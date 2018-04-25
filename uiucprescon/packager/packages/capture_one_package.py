import logging
import os
import shutil
import typing
from . import collection_builder
from uiucprescon.packager.packages.collection import Package, Metadata
from .abs_package_builder import AbsPackageBuilder


class CaptureOnePackage(AbsPackageBuilder):

    def locate_packages(self, batch_path) -> typing.Iterator[Package]:
        for package in collection_builder.build_capture_one_batch(batch_path):
            yield package

    def transform(self, package: Package, dest: str) -> None:
        logger = logging.getLogger(__name__)
        logger.setLevel(AbsPackageBuilder.log_level)

        for item in package:
            item_name = item.metadata[Metadata.ITEM_NAME]
            object_name = item.metadata[Metadata.ID]
            for inst in item:
                assert len(inst.files) == 1
                for file_ in inst.files:
                    _, ext = os.path.splitext(file_)
                    new_file_name = "{}_{}{}".format(object_name, item_name,
                                                     ext)
                    new_file_path = os.path.join(dest, new_file_name)

                    logger.debug(
                        "Copying {} to {}".format(file_, new_file_path)
                    )

                    shutil.copy(file_, new_file_path)

                    logger.info("Added {} to {}".format(
                        new_file_name, new_file_path))
