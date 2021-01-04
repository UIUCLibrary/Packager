"""Package generated from the lab using Capture One."""

import logging
import os
import typing
from uiucprescon.packager import transformations
from uiucprescon.packager.common import Metadata
from uiucprescon.packager.packages.collection import Package
from . import collection_builder
from .abs_package_builder import AbsPackageBuilder


class CaptureOnePackage(AbsPackageBuilder):
    """Package generated from the lab using Capture One.

  + batch folder
      - uniqueID1_00000001.tif
      - uniqueID1_00000002.tif
      - uniqueID1_00000003.tif
      - uniqueID2_00000001.tif
      - uniqueID2_00000002.tif
"""

    def locate_packages(self, path) -> typing.Iterator[Package]:

        builder = collection_builder.CaptureOneBuilder()
        for package in builder.build_batch(path):
            yield package

    def transform(self, package: Package, dest: str) -> None:
        logger = logging.getLogger(__name__)
        logger.setLevel(AbsPackageBuilder.log_level)

        for item in package:
            item_name = item.metadata[Metadata.ITEM_NAME]
            object_name = item.metadata[Metadata.ID]
            for inst in item:
                if len(inst.files) != 1:
                    raise AssertionError("More than one file found")
                for file_ in inst.files:
                    _, ext = os.path.splitext(file_)
                    new_file_name = "{}_{}{}".format(object_name, item_name,
                                                     ext)

                    copy = transformations.Transformers(
                        strategy=transformations.CopyFile(),
                        logger=logger
                    )
                    new_file_path = os.path.join(dest, new_file_name)
                    copy.transform(source=file_, destination=new_file_path)
