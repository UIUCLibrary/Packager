import logging
import os
import shutil
import typing
try:
    import pykdu_compress
except ImportError as e:
    print("Unable to use transform DigitalLibraryCompound due to "
          "missing import")

from . import collection_builder
from uiucprescon.packager.packages.collection import Package, Metadata
from .abs_package_builder import AbsPackageBuilder


class DigitalLibraryCompound(AbsPackageBuilder):

    def locate_packages(self, path) -> typing.Iterator[Package]:

        for package in \
                collection_builder.build_digital_library_compound_batch(path):

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
                assert len(inst.files) == 1
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

                    logger.debug(
                        "Copying {} to {}".format(
                            file_, new_preservation_file_path
                        )
                    )

                    shutil.copy(file_, new_preservation_file_path)
                    logger.info("Added {}".format(file_))

                    # Convert
                    access_file = "{}.jp2".format(base_name)

                    make_access_jp2(file_, os.path.join(access_path,
                                                        access_file))

                    logger.info("Generated {}".format(access_file))


def make_access_jp2(source_file_path, output_file_name):
    pykdu_compress.kdu_compress_cli(
        "-i {} -o {}".format(source_file_path, output_file_name))
