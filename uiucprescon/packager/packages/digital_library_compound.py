import logging
import os

import typing

from uiucprescon.packager.packages.collection import Package
from uiucprescon.packager.common import Metadata, InstantiationTypes
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

    .. versionchanged:: 0.1.3
        Possible to transform packages that contain images in a compressed file

    """

    def locate_packages(self, path) -> typing.Iterator[Package]:
        builder = collection_builder.DigitalLibraryCompoundBuilder()

        for package in builder.build_batch(path):
            yield package

    @staticmethod
    def _get_transformer(logger, package_builder, destination_root):
        return Transform(logger, package_builder,
                         destination_root=destination_root)

    def transform(self, package: Package, dest: str) -> None:
        logger = logging.getLogger(__name__)
        logger.setLevel(AbsPackageBuilder.log_level)

        for item in package:
            item_name = item.metadata[Metadata.ITEM_NAME]
            object_name = item.metadata[Metadata.ID]

            transformer = self._get_transformer(logger, self,
                                                destination_root=dest)

            for inst in item:
                if len(inst.files) != 1:
                    raise AssertionError(
                        f"Each instance should have only 1 file, found "
                        f"{inst.files}: [{', '.join(inst.files)}]")

                for file_ in inst.get_files():

                    if inst.category == InstantiationTypes.SUPPLEMENTARY:
                        transformer.transform_supplementary_data(file_,
                                                                 item_name,
                                                                 object_name)
                        continue

                    transformer.transform_preservation_file(file_, item_name,
                                                            object_name)

                    transformer.transform_access_file(file_, item_name,
                                                      object_name)

    @staticmethod
    def get_file_base_name(item_name, object_name):
        new_base_name = f"{object_name}_{item_name}"
        return new_base_name


class Transform:
    _strategies = {
        'CopyFile': transformations.CopyFile(),
        'ConvertJp2Standard': transformations.ConvertJp2Standard(),
        'ConvertTiff': transformations.ConvertTiff()
    }

    def __init__(self, logger, package_builder: DigitalLibraryCompound,
                 destination_root) -> None:

        self._package_builder = package_builder
        self.logger = logger
        self.destination_root = destination_root

    def transform_supplementary_data(self, src: str, item_name: str,
                                     object_name: str):
        """Transform the supplementary file

       Args:
            src: supplementary file to be used
            item_name: Item name of that the file belongs to
            object_name: Object name of that the file belongs to

        Returns:

        """

        supplementary_dir = os.path.join(
            self.destination_root,
            object_name,
            InstantiationTypes.SUPPLEMENTARY.value  # pylint: disable=no-member
        )

        if not os.path.exists(supplementary_dir):
            os.makedirs(supplementary_dir)

        base_name = self._package_builder.get_file_base_name(
            item_name, object_name)
        ext = os.path.splitext(src)[1]
        new_file = os.path.join(supplementary_dir, f"{base_name}{ext}")

        copier = transformations.Transformers(
            strategy=self._strategies['CopyFile'],
            logger=self.logger
        )
        copier.transform(src, new_file)

    def transform_access_file(self, src: str, item_name: str,
                              object_name: str):
        """Transform the file into an access file

        Args:
            src: file to be used to generate the access file
            item_name: Item name of that the file belongs to
            object_name: Object name of that the file belongs to

        Returns:

        """

        access_path = os.path.join(
            self.destination_root,
            object_name,
            InstantiationTypes.ACCESS.value  # pylint: disable=no-member
        )
        if not os.path.exists(access_path):
            os.makedirs(access_path)

        access_file = "{}.jp2".format(
            self._package_builder.get_file_base_name(item_name, object_name)
        )

        access_file_full_path = os.path.join(access_path, access_file)
        ext = os.path.splitext(src)[1]
        if ext.lower() == ".jp2":
            access_file_maker = transformations.Transformers(
                strategy=self._strategies['CopyFile'],
                logger=self.logger)

        elif ext.lower() == ".tif":
            access_file_maker = transformations.Transformers(
                strategy=self._strategies['ConvertJp2Standard'],
                logger=self.logger)
        else:
            raise ValueError("Unknown extension {}".format(ext))

        access_file_maker.transform(src, access_file_full_path)

    def transform_preservation_file(self, src, item_name, object_name):

        preservation_path = os.path.join(
            self.destination_root,
            object_name,
            InstantiationTypes.PRESERVATION.value  # pylint: disable=no-member
        )

        if not os.path.exists(preservation_path):
            os.makedirs(preservation_path)

        new_base_name = self._package_builder.get_file_base_name(
            item_name, object_name)

        new_preservation_file_path = \
            os.path.join(self.destination_root,
                         object_name,
                         "preservation",
                         f"{new_base_name}.tif")

        ext = os.path.splitext(src)[1]
        if ext.lower() == ".jp2":

            preservation_file_copier = transformations.Transformers(
                strategy=self._strategies['ConvertTiff'],
                logger=self.logger
            )

        elif ext.lower() == ".tif":
            preservation_file_copier = transformations.Transformers(
                strategy=self._strategies['CopyFile'],
                logger=self.logger)
        else:
            raise ValueError("Unknown extension {}".format(ext))

        preservation_file_copier.transform(
            source=src, destination=new_preservation_file_path)
