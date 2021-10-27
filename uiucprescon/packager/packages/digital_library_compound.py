"""Compound objects for the Medusa Digital Library."""
import abc
import logging
import os

import typing

from uiucprescon.packager.packages.collection import \
    Instantiation, Package, Item

from uiucprescon.packager.common import Metadata, InstantiationTypes
from uiucprescon.packager import transformations
from . import collection_builder
from .abs_package_builder import AbsPackageBuilder

__all__ = [
    'DigitalLibraryCompound'
]


class AbsItemTransformStrategy(abc.ABC):

    def __init__(self, logger: typing.Optional[logging.Logger] = None) -> None:
        self.logger = logger or logging.getLogger(__name__)
        super().__init__()

    @abc.abstractmethod
    def transform_preservation_file(
            self,
            item: Item,
            dest: str,
            logger: typing.Optional[logging.Logger]
    ) -> None:
        pass

    @abc.abstractmethod
    def transform_access_file(
            self,
            item: Item,
            dest: str,
            logger: typing.Optional[logging.Logger]
    ) -> None:
        pass

    @abc.abstractmethod
    def transform_supplementary_data(
            self,
            instance: Item,
            dest: str,
            logger: typing.Optional[logging.Logger]
    ) -> None:
        pass

    def process(
            self,
            source: str,
            dest: str,
            strategy: typing.Type[transformations.AbsTransformation],
            logger: logging.Logger
    ) -> None:
        transformer = strategy()
        output_path = os.path.split(dest)[0]
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        transformer.transform(source, dest, logger)


class DigitalLibraryTransformItem:

    def __init__(self, strategy: AbsItemTransformStrategy) -> None:
        super().__init__()
        self._strategy = strategy

    def transform_supplementary_data(
            self,
            item: Item,
            dest: str,
            logger: typing.Optional[logging.Logger]
    ) -> None:
        self._strategy.transform_supplementary_data(item, dest, logger)

    def transform_preservation_file(
            self,
            item: Item,
            dest: str,
            logger: typing.Optional[logging.Logger] = None
    ) -> None:
        logger = logger or logging.getLogger(__name__)
        self._strategy.transform_preservation_file(item, dest, logger)

    def transform_access_file(
            self,
            item: Item,
            dest: str,
            logger: typing.Optional[logging.Logger]
    ) -> None:
        self._strategy.transform_access_file(item, dest, logger)


class UseAccessJp2ForAll(AbsItemTransformStrategy):

    def transform_preservation_file(self, item: Item, dest: str,
                                    logger: typing.Optional[
                                        logging.Logger]) -> None:

        access = item.instantiations[InstantiationTypes.ACCESS]
        access_files: typing.List[str] = list(access.get_files())
        if len(access_files) > 1:
            raise ValueError(
                f"transform_preservation_file requires item to have exactly "
                f"one access instance file, "
                f"found {len(access_files)}"
            )
        access_file = access_files[0]
        mmsid = item.metadata[Metadata.ID]
        item_id = access.metadata[Metadata.ITEM_NAME]
        new_file_name = f"{mmsid}-{item_id}.tif"

        logger = logger or logging.getLogger(__name__)

        logger.warning(
            "Creating preservation file '%s' from access file '%s'.",
            new_file_name,
            access_file
        )

        self.process(
            source=access_file,
            dest=os.path.join(
                dest,
                typing.cast(str, item.metadata[Metadata.ID]),
                "preservation",
                new_file_name
            ),
            strategy=transformations.ConvertTiff,
            logger=logger
        )

    def transform_access_file(self, item: Item, dest: str,
                              logger: typing.Optional[logging.Logger]) -> None:
        logger = logger or logging.getLogger(__name__)
        access = item.instantiations[InstantiationTypes.ACCESS]
        access_files: typing.List[str] = list(access.get_files())
        if len(access_files) > 1:
            raise ValueError(
                f"transform_preservation_file requires item to have exactly "
                f"one access instance file, "
                f"found {len(access_files)}"
            )
        access_file = access_files[0]
        mmsid = item.metadata[Metadata.ID]
        item_id = access.metadata[Metadata.ITEM_NAME]
        new_file_name = f"{mmsid}-{item_id}.jp2"

        self.process(
            source=access_file,
            dest=os.path.join(
                dest,
                typing.cast(str, item.metadata[Metadata.ID]),
                "access",
                new_file_name
            ),
            strategy=transformations.CopyFile,
            logger=logger
        )

    def transform_supplementary_data(self, instance: Item, dest: str,
                                     logger: typing.Optional[
                                         logging.Logger]) -> None:
        logger = logger or logging.getLogger(__name__)
        supplementary = \
            instance.instantiations.get(
                InstantiationTypes.SUPPLEMENTARY
            )
        if supplementary is None:
            return

        files: typing.Iterable[str] = supplementary.get_files()

        for file in files:
            new_file_name = os.path.split(file)[-1]
            self.process(
                source=file,
                dest=os.path.join(
                    dest,
                    typing.cast(str, instance.metadata[Metadata.ID]),
                    "supplementary",
                    new_file_name
                ),
                strategy=transformations.CopyFile,
                logger=logger
            )


class UseAccessTiffs(AbsItemTransformStrategy):
    """Access tiff files to generate access jp2.

    Output preservation files use preservation files
    """

    def transform_preservation_file(
            self,
            item: Item,
            dest: str,
            logger: typing.Optional[logging.Logger] = None
    ) -> None:
        logger = logger or logging.getLogger(__name__)
        preservation = item.instantiations[InstantiationTypes.PRESERVATION]
        preservation_files: typing.List[str] = list(preservation.get_files())

        if len(preservation_files) > 1:
            raise ValueError(
                f"transform_preservation_file requires item to have exactly "
                f"one preservation instance file, "
                f"found {len(preservation_files)}"
            )

        preservation_file = preservation_files[0]
        mmsid = item.metadata[Metadata.ID]
        item_id = preservation.metadata[Metadata.ITEM_NAME]
        new_file_name = f"{mmsid}-{item_id}.tif"
        self.process(
            source=preservation_file,
            dest=os.path.join(
                dest,
                typing.cast(str, item.metadata[Metadata.ID]),
                "preservation",
                new_file_name
            ),
            strategy=transformations.CopyFile,
            logger=logger
        )

    def transform_access_file(
            self,
            item: Item,
            dest: str,
            logger: typing.Optional[logging.Logger] = None
    ) -> None:
        logger = logger or logging.getLogger(__name__)
        access = item.instantiations[InstantiationTypes.ACCESS]
        access_files: typing.List[str] = list(access.get_files())

        if len(access_files) > 1:
            raise ValueError(
                f"transform_preservation_file requires item to have exactly "
                f"one preservation instance file, "
                f"found {len(access_files)}"
            )

        access_file = access_files[0]
        mmsid = item.metadata[Metadata.ID]
        item_id = access.metadata[Metadata.ITEM_NAME]
        new_file_name = f"{mmsid}-{item_id}.jp2"
        self.process(
            source=access_file,
            dest=os.path.join(
                dest,
                typing.cast(str, item.metadata[Metadata.ID]),
                "access",
                new_file_name
            ),
            strategy=transformations.ConvertJp2Standard,
            logger=logger
        )

    def transform_supplementary_data(
            self,
            item: Item,
            dest: str,
            logger: typing.Optional[logging.Logger] = None
    ) -> None:
        logger = logger or logging.getLogger(__name__)
        supplementary = \
            item.instantiations.get(
                InstantiationTypes.SUPPLEMENTARY
            )
        if supplementary is None:
            return

        files: typing.Iterable[str] = supplementary.get_files()

        for file in files:
            new_file_name = os.path.split(file)[-1]
            self.process(
                source=file,
                dest=os.path.join(
                    dest,
                    typing.cast(str, item.metadata[Metadata.ID]),
                    "supplementary",
                    new_file_name
                ),
                strategy=transformations.CopyFile,
                logger=logger
            )


class UsePreservationForAll(AbsItemTransformStrategy):
    """Use source preservation file for generating access & preservation files.

    Access jp2s and preservation tiff files use the same source file.
    """

    def __init__(
            self,
            package_builder: "DigitalLibraryCompound",
    ) -> None:
        super().__init__()
        self.package_builder = package_builder

    @staticmethod
    def _get_transformer(
            logger: logging.Logger,
            package_builder: "DigitalLibraryCompound",
            destination_root: str
    ) -> "Transform":
        return Transform(logger, package_builder,
                         destination_root=destination_root)

    def transform_preservation_file(
            self,
            item: Item,
            dest: str,
            logger: typing.Optional[logging.Logger]
    ) -> None:
        transformer = self._get_transformer(
            logger=self.logger or logging.getLogger(__name__),
            package_builder=self.package_builder,
            destination_root=dest
        )
        item_name = typing.cast(str, item.metadata[Metadata.ITEM_NAME])
        object_name = typing.cast(str, item.metadata[Metadata.ID])

        instance: Instantiation
        for instance in item:

            file_: str
            files: typing.List[str] = instance.get_files()
            for file_ in files:
                if instance.category == InstantiationTypes.SUPPLEMENTARY:
                    continue

                transformer.transform_preservation_file(
                    file_,
                    item_name,
                    object_name
                )

    def transform_access_file(
            self,
            item: Item,
            dest: str,
            logger: typing.Optional[logging.Logger]
    ) -> None:
        item_name = typing.cast(str, item.metadata[Metadata.ITEM_NAME])
        object_name = typing.cast(str, item.metadata[Metadata.ID])

        transformer = self._get_transformer(
            logger=self.logger or logging.getLogger(__name__),
            package_builder=self.package_builder,
            destination_root=dest
        )

        instance: Instantiation
        for instance in item:
            for file_ in instance.get_files():
                if instance.category == InstantiationTypes.SUPPLEMENTARY:
                    continue

                transformer.transform_access_file(
                    file_,
                    item_name,
                    object_name
                )

    def transform_supplementary_data(
            self,
            item: Item,
            dest: str,
            logger: typing.Optional[logging.Logger]
    ) -> None:
        item_name = typing.cast(str, item.metadata[Metadata.ITEM_NAME])
        object_name = typing.cast(str, item.metadata[Metadata.ID])

        instance: Instantiation
        for instance in item:
            if instance.category != InstantiationTypes.SUPPLEMENTARY:
                continue
            transformer = self._get_transformer(
                logger=self.logger or logging.getLogger(__name__),
                package_builder=self.package_builder,
                destination_root=dest
            )

            file_: str
            for file_ in instance.get_files():
                transformer.transform_supplementary_data(
                    file_,
                    item_name,
                    object_name
                )


class DigitalLibraryCompound(AbsPackageBuilder):
    """For submitting to UIUC Digital library with the compound object profile.

     + uniqueID1 (folder)
         + preservation (folder)
             - uniqueID1-00000001.tif
             - uniqueID1-00000002.tif
             - uniqueID1-00000003.tif
         + access (folder)
             - uniqueID1-00000001.jp2
             - uniqueID1-00000002.jp2
             - uniqueID1-00000003.jp2
     + uniqueID2 (folder)
         + preservation (folder)
             - uniqueID2-00000001.tif
             - uniqueID2-00000002.tif
         + access (folder)
             - uniqueID2=00000001.jp2
             - uniqueID2-00000002.jp2

    .. versionchanged:: 0.1.3
        Possible to transform packages that contain images in a compressed file

    .. versionchanged:: 0.2.11
        Files in preservation and access don't have a group id in them.
            Instead of uniqueID2/access/uniqueID2_00000001.jp2, it is
            uniqueID2/access/uniqueID2-00000001.jp2

    .. versionchanged:: 0.2.12
        DigitalLibraryCompound can have files with multiple volume file names.

    """

    def locate_packages(self, path: str) -> typing.Iterator[Package]:
        """Locate Digital Library packages on a given file path.

        Args:
            path: File path to search for Digital Library packages

        Yields:
            Digital Library packages

        """
        builder = collection_builder.DigitalLibraryCompoundBuilder()

        yield from builder.build_batch(path)

    @staticmethod
    def _get_transformer(
            logger: logging.Logger,
            package_builder: "DigitalLibraryCompound",
            destination_root: str
    ) -> "Transform":
        return Transform(logger, package_builder,
                         destination_root=destination_root)

    def transform(self, package: Package, dest: str) -> None:
        """Transform package into a Digital library package.

        Args:
            package: Source package to transform
            dest: File path to save the transformed package

        """
        logger: logging.Logger = logging.getLogger(__name__)
        logger.setLevel(AbsPackageBuilder.log_level)

        item: Item
        for item in package:
            self.transform_one_item(item, dest, logger=logger)

    def transform_one_item(
            self,
            item: Item,
            dest: str,
            transformation_strategy: AbsItemTransformStrategy = None,
            logger: typing.Optional[logging.Logger] = None
    ) -> None:
        """Transform a single item."""
        strategy = \
            transformation_strategy or \
            self._get_item_transformer_strategy(item)

        transformer = \
            DigitalLibraryTransformItem(strategy)

        transformer.transform_supplementary_data(item, dest, logger)
        transformer.transform_preservation_file(item, dest, logger)
        transformer.transform_access_file(item, dest, logger)

    @staticmethod
    def get_file_base_name(item_name: str) -> str:
        """Get the base name of a file, without an extension."""
        return f"{item_name}"

    def _get_item_transformer_strategy(
            self,
            item: Item
    ) -> AbsItemTransformStrategy:

        access = item.instantiations.get(InstantiationTypes.ACCESS)
        if access is None:
            return UsePreservationForAll(
                package_builder=self,
            )
        if any(file.lower().endswith(".jp2") for file in access.files):
            return UsePreservationForAll(
                package_builder=self,
            )
        # If no preservation files, generate them with the access files
        preservation = item.instantiations.get(InstantiationTypes.PRESERVATION)
        if preservation is None:
            return UseAccessJp2ForAll()
        return UseAccessTiffs()


class Transform:
    """Helper for transforming files."""

    _strategies = {
        'CopyFile': transformations.CopyFile(),
        'ConvertJp2Standard': transformations.ConvertJp2Standard(),
        'ConvertTiff': transformations.ConvertTiff()
    }

    def __init__(
            self,
            logger: logging.Logger,
            package_builder: DigitalLibraryCompound,
            destination_root: str
    ) -> None:
        """Create a new Helper object for transforming files.

        Args:
            logger: System logger to use
            package_builder:
            destination_root:
        """
        self._package_builder = package_builder
        self.logger = logger
        self.destination_root = destination_root

    def transform_supplementary_data(
            self,
            src: str,
            item_name: str,
            object_name: str
    ) -> None:
        """Transform the supplementary file.

        Args:
            src: supplementary file to be used
            item_name: Item name of that the file belongs to
            object_name: Object name of that the file belongs to

        """
        supplementary_dir = os.path.join(
            self.destination_root,
            object_name,
            InstantiationTypes.SUPPLEMENTARY.value  # pylint: disable=no-member
        )

        if not os.path.exists(supplementary_dir):
            os.makedirs(supplementary_dir)

        base_name = self._package_builder.get_file_base_name(item_name)
        ext = os.path.splitext(src)[1]
        new_file = os.path.join(
            supplementary_dir,
            f"{object_name}-{base_name}{ext}"
        )

        copier = transformations.Transformers(
            strategy=self._strategies['CopyFile'],
            logger=self.logger
        )
        copier.transform(src, new_file)

    def transform_access_file(
            self,
            src: str,
            item_name: str,
            object_name: str,
    ) -> None:
        """Transform the file into an access file.

        Args:
            src: file to be used to generate the access file
            item_name: Item name of that the file belongs to
            object_name: Object name of that the file belongs to

        """
        access_path = os.path.join(
            self.destination_root,
            object_name,
            InstantiationTypes.ACCESS.value  # pylint: disable=no-member
        )
        if not os.path.exists(access_path):
            os.makedirs(access_path)
        item_name_part = self._package_builder.get_file_base_name(item_name)
        access_file = f"{object_name}-{item_name_part}.jp2"

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

    def transform_preservation_file(
            self,
            src: str,
            item_name: str,
            object_name: str
    ) -> None:
        """Transform the source file into a preservation file."""
        preservation_path = os.path.join(
            self.destination_root,
            object_name,
            InstantiationTypes.PRESERVATION.value  # pylint: disable=no-member
        )

        if not os.path.exists(preservation_path):
            os.makedirs(preservation_path)

        new_base_name = self._package_builder.get_file_base_name(item_name)

        new_preservation_file_path = \
            os.path.join(self.destination_root,
                         object_name,
                         "preservation",
                         f"{object_name}-{new_base_name}.tif")

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
