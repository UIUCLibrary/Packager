import logging
import os
import shutil
import typing
from . import collection_builder
from packager.packages.collection import Package
from .abs_package_builder import AbsPackageBuilder


class CaptureOnePackage(AbsPackageBuilder):

    def locate_packages(self, batch_path) -> typing.Iterator[Package]:
        for package in collection_builder.build_capture_one_batch(batch_path):
            yield package

    def transform(self, package: Package, dest: str) -> None:
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)

        for item in package:
            item_name = item.metadata['item_name']
            object_name = item.metadata['id']
            for inst in item:
                assert len(inst.files) == 1
                for file_ in inst.files:
                    _, ext = os.path.splitext(file_)
                    new_file_name = "{}_{}{}".format(object_name, item_name, ext)
                    new_file_path = os.path.join(dest, new_file_name)
                    logger.info("Copying {} to {}".format(file_, new_file_path ))
                    shutil.copy(file_, new_file_path)