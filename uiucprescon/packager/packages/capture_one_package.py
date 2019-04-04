import logging
import os
import typing
from . import collection_builder
from uiucprescon.packager.packages.collection import Package
from .abs_package_builder import AbsPackageBuilder

from uiucprescon.packager import transformations
from uiucprescon.packager.common import Metadata


class CaptureOnePackage(AbsPackageBuilder):

    def locate_packages(self, batch_path) -> typing.Iterator[Package]:

        builder = collection_builder.CaptureOneBuilder()
        for package in builder.build_batch(batch_path):
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

                    copy = transformations.Transformers(
                        strategy=transformations.CopyFile(),
                        logger=logger
                    )
                    new_file_path = os.path.join(dest, new_file_name)
                    copy.transform(source=file_, destination=new_file_path)
