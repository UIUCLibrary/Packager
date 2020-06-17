import logging
import os

import typing

from uiucprescon.packager.packages.collection import Package
from uiucprescon.packager.common import Metadata
from uiucprescon.packager import transformations
from . import collection_builder
from .abs_package_builder import AbsPackageBuilder


class DigitalLibraryCompound(AbsPackageBuilder):
    """Packaged files for submitting to UIUC Digital library with the compound
    object profile

     + uniqueID1 (folder)
         + preservation (folder)
             - uniqueID1_00000001.tif
             - uniqueID1_00000002.tif
             - uniqueID1_00000003.tif
         + access (folder)
             - uniqueID1_00000001.jp2
             - uniqueID1_00000002.jp2
             - uniqueID1_00000003.jp2
     + uniqueID2 (folder)
         + preservation (folder)
             - uniqueID2_00000001.tif
             - uniqueID2_00000002.tif
         + access (folder)
             - uniqueID2_00000001.jp2
             - uniqueID2_00000002.jp2
    """

    def locate_packages(self, path) -> typing.Iterator[Package]:
        builder = collection_builder.DigitalLibraryCompoundBuilder()

        for package in builder.build_batch(path):
            yield package

    def transform(self, package: Package, dest: str) -> None:
        logger = logging.getLogger(__name__)
        logger.setLevel(AbsPackageBuilder.log_level)

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
                if len(inst.files) != 1:
                    raise AssertionError(
                        f"Each instance should have only 1 file, found "
                        f"{inst.files}: [{', '.join(inst.files)}]")

                for file_ in inst.files:
                    base_name, ext = os.path.splitext(os.path.basename(file_))
                    category = inst.category

                    new_file_name = "{}_{}{}".format(object_name,
                                                     item_name,
                                                     ext)

                    new_preservation_file_path = os.path.join(dest,
                                                              object_name,
                                                              category.value,
                                                              new_file_name)

                    copier = transformations.Transformers(
                        strategy=transformations.CopyFile(),
                        logger=logger
                    )

                    copier.transform(source=file_,
                                     destination=new_preservation_file_path)

                    access_file = "{}.jp2".format(base_name)

                    access_file_full_path = os.path.join(access_path,
                                                         access_file)

                    converter = transformations.Transformers(
                        strategy=transformations.ConvertJp2Standard(),
                        logger=logger)

                    converter.transform(file_, access_file_full_path)
