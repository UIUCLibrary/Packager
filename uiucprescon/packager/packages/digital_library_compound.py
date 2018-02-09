import logging
import os
import shutil
import typing

from . import collection_builder
from uiucprescon.packager.packages.collection import Package, Metadata
from .abs_package_builder import AbsPackageBuilder


class DigitalLibraryCompound(AbsPackageBuilder):

    def locate_packages(self, path) -> typing.Iterator[Package]:
        for package in collection_builder.build_digital_library_compound_batch(path):
            yield package

    def transform(self, package: Package, dest: str) -> None:
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)

        for item in package:
            item_name = item.metadata[Metadata.ITEM_NAME]
            object_name = item.metadata[Metadata.ID]

            access_path = os.path.join(dest, object_name, "access")
            preservation_path = os.path.join(dest, object_name, "preservation")

            if not os.path.exists(access_path):
                os.makedirs(access_path)

            if not os.path.exists(preservation_path):
                os.makedirs(preservation_path)

            for inst in item:
                assert len(inst.files) == 1
                for file_ in inst.files:
                    _, ext = os.path.splitext(file_)
                    category = inst.category
                    new_file_name = "{}_{}{}".format(object_name, item_name, ext)
                    new_file_path = os.path.join(dest, object_name, category.value, new_file_name)
                    logger.info("Copying {} to {}".format(file_, new_file_path))
                    shutil.copy(file_, new_file_path)
