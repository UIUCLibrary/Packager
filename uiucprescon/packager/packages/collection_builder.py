"""Collection builder."""
# pylint: disable=unsubscriptable-object
import abc
import itertools
import logging
import os
import re
import warnings
import zipfile
from typing import Tuple, Optional, Iterator, Iterable, List

from uiucprescon.packager.common import Metadata, PackageTypes
from uiucprescon.packager.common import InstantiationTypes
from .collection import \
    Instantiation, \
    Item, \
    Package, \
    PackageObject, \
    AbsPackageComponent


def _build_ds_instance(item, name: str, path: str) -> None:
    warnings.warn("Use DSBuilder.build_instance instead",
                  PendingDeprecationWarning)

    new_instantiation = Instantiation(category=InstantiationTypes.ACCESS,
                                      parent=item)

    for file in filter(lambda i: i.is_file(), os.scandir(path)):
        if os.path.splitext(os.path.basename(file))[0] == name:
            new_instantiation.files.append(file.path)


def _build_ds_items(package, path: str) -> None:
    logger = logging.getLogger(__name__)

    files = sorted(set(
        map(lambda item: os.path.splitext(item)[0], os.listdir(path)))
    )

    for unique_item in files:
        logger.debug(unique_item)
        new_item = Item(parent=package)
        new_item.component_metadata[Metadata.ITEM_NAME] = unique_item
        _build_ds_instance(new_item, name=unique_item, path=path)


def _build_ds_object(parent_batch, path: str) -> None:
    warnings.warn("Use DSBuilder.build_package instead",
                  PendingDeprecationWarning)
    for folder in filter(lambda i: i.is_dir(), os.scandir(path)):
        new_package = PackageObject(parent=parent_batch)
        new_package.component_metadata[Metadata.PATH] = folder.path
        new_package.component_metadata[Metadata.ID] = folder.name
        new_package.component_metadata[Metadata.TITLE_PAGE] = None
        _build_ds_items(new_package, path=folder.path)


def build_ds_batch(root: str):
    """Build a ds batch.

    Args:
        root: Root path where the batch is located.
    Returns:
        DS Batch

    """
    warnings.warn("Use DSBuilder.build_batch instead ",
                  PendingDeprecationWarning)

    new_batch = Package(root)
    new_batch.component_metadata[Metadata.PATH] = root

    new_batch.component_metadata[Metadata.PACKAGE_TYPE] = \
        PackageTypes.DS_HATHI_TRUST_SUBMISSION

    _build_ds_object(parent_batch=new_batch, path=root)
    return new_batch


def build_bb_instance(new_item, path: str, name: str) -> None:
    """Build a brittle books instance.

    Args:
        new_item:
        path: Root path where the instance is located.
        name:

    """
    warnings.warn("Use BrittleBooksBuilder.build_instance instead ",
                  PendingDeprecationWarning)
    new_instantiation = Instantiation(category=InstantiationTypes.ACCESS,
                                      parent=new_item)

    for file in filter(lambda i: i.is_file(), os.scandir(path)):
        if os.path.splitext(os.path.basename(file))[0] == name:
            new_instantiation.files.append(file.path)


def build_bb_package(new_package, path: str) -> None:
    """Build a brittle books new_package.

    Args:
        new_package:
        path: Root path where the package is located.

    Returns:
        Brittle books package

    """
    warnings.warn("Use BrittleBooksBuilder.build_package instead ",
                  PendingDeprecationWarning)
    logger = logging.getLogger(__name__)
    files = set(map(lambda item: os.path.splitext(item)[0], os.listdir(path)))
    for unique_item in sorted(files):
        logger.debug(unique_item)
        new_item = Item(parent=new_package)
        new_item.component_metadata[Metadata.ITEM_NAME] = unique_item
        build_bb_instance(new_item, name=unique_item, path=path)


def build_bb_batch(root: str) -> Package:
    """Build a brittle books batch.

    Args:
        root: Root path where the batch is located.

    Returns:
        Brittle books batch

    """
    warnings.warn("Use BrittleBooksBuilder.build_batch instead ",
                  PendingDeprecationWarning)

    logger = logging.getLogger(__name__)
    new_batch = Package(root)
    for directory in filter(lambda i: i.is_dir(), os.scandir(root)):
        logger.debug("scanning %s", directory.path)
        new_object = PackageObject(parent=new_batch)
        new_object.component_metadata[Metadata.PATH] = directory.path
        new_object.component_metadata[Metadata.ID] = directory.name

        new_object.component_metadata[Metadata.PACKAGE_TYPE] = \
            PackageTypes.BRITTLE_BOOKS_HATHI_TRUST_SUBMISSION

        build_bb_package(new_object, path=directory.path)
    return new_batch


class AbsCollectionBuilder(metaclass=abc.ABCMeta):
    """AbsCollectionBuilder.

    .. versionchanged :: 0.2.11
        Many of the abstract methods are no longer class methods.

    """

    @abc.abstractmethod
    def build_batch(self, root: str) -> AbsPackageComponent:
        """Build a new batch of a given packaging type.

        .. versionchanged :: 0.2.11
            Changed from a class method to an instanced method
        """

    @abc.abstractmethod
    def build_instance(
            self,
            parent,
            path: str,
            filename: str,
            *args,
            **kwargs
    ) -> None:
        """Build an instance and add it to the parent.

        Args:
            parent:
            path:
            filename:
            *args:
            **kwargs:

        .. versionchanged :: 0.2.11
            Changed from a class method to an instanced method

        """

    @abc.abstractmethod
    def build_package(self, parent, path: str, *args, **kwargs) -> None:
        """Build a pckage.

        Args:
            parent:
            path:

        .. versionchanged :: 0.2.11
            Changed from a class method to an instanced method

        """

    @staticmethod
    def filter_same_name_files(item: "os.DirEntry[str]",
                               filename: str) -> bool:

        if not item.is_file():
            return False

        base, _ = os.path.splitext(item.name)

        return base == filename

    @staticmethod
    def filter_nonsystem_files_only(item: "os.DirEntry[str]") -> bool:
        """Filter out nonsystem files.

        Args:
            item: DirEntry from scandir

        Returns:
            Returns True if the item is a file that is not a a system file.

        """
        system_files = [
            "Thumbs.db",
            "desktop.ini",
            ".DS_Store"
        ]

        if not item.is_file():
            return False
        return item.name not in system_files


class DSBuilder(AbsCollectionBuilder):
    """DSBuilder."""

    def build_batch(self, root: str) -> AbsPackageComponent:
        new_batch = Package(root)
        new_batch.component_metadata[Metadata.PATH] = root

        new_batch.component_metadata[Metadata.PACKAGE_TYPE] = \
            PackageTypes.DS_HATHI_TRUST_SUBMISSION

        self.build_package(parent=new_batch, path=root)
        return new_batch

    def build_instance(
            self,
            parent,
            path: str,
            filename: str,
            *args,
            **kwargs
    ) -> None:

        new_instantiation = Instantiation(category=InstantiationTypes.ACCESS,
                                          parent=parent)

        for file in filter(lambda i: i.is_file(), os.scandir(path)):
            if os.path.splitext(os.path.basename(file))[0] == filename:
                new_instantiation.files.append(file.path)

    def build_package(self, parent, path: str, *args, **kwargs) -> None:
        for folder in filter(lambda i: i.is_dir(), os.scandir(path)):
            new_package = PackageObject(parent=parent)
            new_package.component_metadata[Metadata.PATH] = folder.path
            new_package.component_metadata[Metadata.ID] = folder.name
            new_package.component_metadata[Metadata.TITLE_PAGE] = None
            self._build_ds_items(new_package, path=folder.path)

    def _build_ds_items(self, parent, path: str) -> None:
        logger = logging.getLogger(__name__)

        files = sorted(set(
            map(lambda item: os.path.splitext(item)[0], os.listdir(path)))
        )

        for unique_item in files:
            logger.debug(unique_item)
            new_item = Item(parent=parent)
            new_item.component_metadata[Metadata.ITEM_NAME] = unique_item
            self.build_instance(new_item, filename=unique_item, path=path)


class BrittleBooksBuilder(AbsCollectionBuilder):
    """BrittleBooksBuilder."""

    def build_instance(
            self,
            parent,
            path: str,
            filename: str,
            *args,
            **kwargs
    ) -> None:
        new_instantiation = Instantiation(
            category=InstantiationTypes.ACCESS,
            parent=parent)

        for file in filter(lambda i: i.is_file(), os.scandir(path)):
            if os.path.splitext(os.path.basename(file))[0] == filename:
                new_instantiation.files.append(file.path)

    def build_package(self, parent, path: str, *args, **kwargs) -> None:
        logger = logging.getLogger(__name__)

        files = set(
            map(lambda item: os.path.splitext(item)[0], os.listdir(path)))

        for unique_item in sorted(files):
            logger.debug(unique_item)
            new_item = Item(parent=parent)
            new_item.component_metadata[Metadata.ITEM_NAME] = unique_item
            self.build_instance(new_item, filename=unique_item, path=path)

    def build_batch(self, root: str) -> AbsPackageComponent:
        logger = logging.getLogger(__name__)
        new_batch = Package(root)
        for directory in filter(lambda i: i.is_dir(), os.scandir(root)):
            logger.debug("scanning %s", directory.path)
            new_object = PackageObject(parent=new_batch)
            new_object.component_metadata[Metadata.PATH] = directory.path
            new_object.component_metadata[Metadata.ID] = directory.name

            new_object.component_metadata[Metadata.PACKAGE_TYPE] = \
                PackageTypes.BRITTLE_BOOKS_HATHI_TRUST_SUBMISSION

            self.build_package(new_object, path=directory.path)
        return new_batch


class HathiTiffBuilder(AbsCollectionBuilder):
    """HathiTiffBuilder."""

    def build_batch(self, root: str) -> AbsPackageComponent:
        new_batch = Package(root)
        new_batch.component_metadata[Metadata.PATH] = root

        for dir_ in filter(lambda i: i.is_dir(), os.scandir(root)):
            new_object = PackageObject(parent=new_batch)
            new_object.component_metadata[Metadata.ID] = dir_.name
            new_object.component_metadata[Metadata.PATH] = dir_.path

            new_object.component_metadata[Metadata.PACKAGE_TYPE] = \
                PackageTypes.HATHI_TRUST_TIFF_SUBMISSION
            self.build_package(new_object, path=dir_.path)

        return new_batch

    @staticmethod
    def filter_tiff_files(item: "os.DirEntry[str]") -> bool:
        """Filter out items that are not a tiff file.

        Args:
            item: DirEntry from scandir

        Returns:
            Returns True if the item is a tiff file else returns False

        """
        if not item.is_file():
            return False

        ext = os.path.splitext(item.name)[1]
        return ext.lower() == ".tif"

    def build_package(self, parent, path: str, *args, **kwargs) -> None:

        for file_ in filter(self.filter_tiff_files, os.scandir(path)):
            new_item = Item(parent=parent)
            item_part, _ = os.path.splitext(file_.name)
            new_item.component_metadata[Metadata.ITEM_NAME] = item_part
            self.build_instance(new_item, path=path, filename=item_part)

    def build_instance(self, parent, path, filename, *args, **kwargs):

        def _organize_files(item: os.DirEntry) -> str:
            ext = os.path.splitext(item.name)[1]
            if ext.lower() == ".tif":
                return "main_files"
            return "sidecar"

        matching_files = \
            filter(lambda x, file_name=filename:
                   self.filter_same_name_files(x, file_name), os.scandir(path))

        sidecar_files = []
        main_files = []
        for key, value in itertools.groupby(
                matching_files, key=_organize_files
        ):
            if key == "sidecar":
                for file_ in value:
                    sidecar_files.append(file_)
            elif key == "main_files":
                for file_ in value:
                    main_files.append(file_)
        new_instantiation = Instantiation(category=InstantiationTypes.ACCESS,
                                          parent=parent,
                                          files=main_files)

        for file_ in sidecar_files:
            new_instantiation.sidecar_files.append(file_.path)


class DigitalLibraryCompoundBuilder(AbsCollectionBuilder):
    """DigitalLibraryCompoundBuilder."""

    def build_batch(self, root: str) -> AbsPackageComponent:

        new_batch = Package(root)
        new_batch.component_metadata[Metadata.PATH] = root

        for dir_ in filter(lambda i: i.is_dir(), os.scandir(root)):
            new_object = PackageObject(parent=new_batch)
            new_object.component_metadata[Metadata.ID] = dir_.name
            new_object.metadata[Metadata.PATH] = dir_.path

            new_object.component_metadata[Metadata.PACKAGE_TYPE] = \
                PackageTypes.DIGITAL_LIBRARY_COMPOUND

            self.build_package(new_object, path=dir_.path)
        return new_batch

    def build_instance(
            self,
            parent,
            path: str,
            filename: str,
            *args,
            **kwargs
    ) -> None:
        access_file = os.path.join(path, "access", filename + ".jp2")

        preservation_file = os.path.join(path, "preservation",
                                         filename + ".tif")

        if not os.path.exists(access_file):
            raise FileNotFoundError(f"Access file {access_file} not found")

        if not os.path.exists(preservation_file):
            raise FileNotFoundError(
                f"Preservation file {preservation_file} not found")

        Instantiation(category=InstantiationTypes.ACCESS,
                      parent=parent,
                      files=[access_file])

        Instantiation(
            category=InstantiationTypes.PRESERVATION,
            parent=parent,
            files=[preservation_file]
        )

    @staticmethod
    def file_type_filter(item: 'os.DirEntry[str]',
                         file_extension: str) -> bool:
        """Filter out files not matching extension."""
        if not item.is_file():
            return False
        _, ext = os.path.splitext(item.name)
        return ext.lower() == file_extension

    def build_package(self, parent, path: str, *args, **kwargs) -> None:
        access_path = os.path.join(path, "access")
        preservation_path = os.path.join(path, "preservation")

        if not os.path.exists(access_path):
            raise FileNotFoundError(f"Access path {access_path} not found")

        if not os.path.exists(preservation_path):
            raise FileNotFoundError(
                f"Preservation path {preservation_path} not found")

        access_files = sorted(
            filter(lambda i: self.file_type_filter(i, ".jp2"),
                   os.scandir(access_path)),
            key=lambda f: f.name)

        preservation_files = sorted(
            filter(lambda i: self.file_type_filter(i, ".tif"),
                   os.scandir(preservation_path)),
            key=lambda f: f.name)

        if len(access_files) != len(preservation_files):
            raise AssertionError("Number of access files do not match the "
                                 "number of preservation files")

        for access_file, preservation_file in \
                zip(access_files, preservation_files):

            if os.path.splitext(access_file.name)[0] != \
                   os.path.splitext(preservation_file.name)[0]:
                raise AssertionError(
                    f"{os.path.splitext(access_file.name)[0]} should be the "
                    f"same name {os.path.splitext(preservation_file.name)[0]}")

            item_id = os.path.splitext(access_file.name)[0]
            new_item = Item(parent=parent)
            self.build_instance(new_item, filename=item_id, path=path)


class HathiJp2Builder(AbsCollectionBuilder):
    """HathiJp2Builder."""

    def build_batch(self, root: str) -> AbsPackageComponent:

        new_batch = Package(root)
        new_batch.component_metadata[Metadata.PATH] = root

        for dir_ in filter(lambda i: i.is_dir(), os.scandir(root)):
            new_object = PackageObject(parent=new_batch)
            new_object.component_metadata[Metadata.ID] = dir_.name
            new_object.component_metadata[Metadata.PATH] = dir_.path

            new_object.component_metadata[Metadata.PACKAGE_TYPE] = \
                PackageTypes.HATHI_TRUST_JP2_SUBMISSION

            self.build_package(new_object, path=dir_.path)

        return new_batch

    @staticmethod
    def filter_tiff_files(item: os.DirEntry) -> bool:
        if not item.is_file():
            return False

        ext = os.path.splitext(item.name)[1]
        return ext.lower() == ".jp2"

    def build_package(self, parent, path: str, *args, **kwargs) -> None:
        for file_ in filter(self.filter_tiff_files, os.scandir(path)):
            new_item = Item(parent=parent)
            item_part, _ = os.path.splitext(file_.name)
            new_item.component_metadata[Metadata.ITEM_NAME] = item_part
            self.build_instance(new_item, path=path, filename=item_part)

    @staticmethod
    def _organize_files(item: os.DirEntry) -> str:
        ext = os.path.splitext(item.name)[1]
        if ext.lower() == ".jp2":
            return "main_files"
        return "sidecar"

    def build_instance(
            self,
            parent,
            path,
            filename,
            *args,
            **kwargs
    ):

        matching_files = \
            filter(lambda x, file_name=filename:
                   self.filter_same_name_files(x, file_name), os.scandir(path))

        sidecar_files = []

        main_files = []
        for key, value in itertools.groupby(
                matching_files,
                key=self._organize_files
        ):
            for file_ in value:
                if key == "sidecar":
                    sidecar_files.append(file_)
                elif key == "main_files":
                    main_files.append(file_)

        new_instantiation = Instantiation(category=InstantiationTypes.ACCESS,
                                          parent=parent,
                                          files=main_files
                                          )

        for file_ in sidecar_files:
            new_instantiation.sidecar_files.append(file_.path)


class HathiLimitedViewBuilder(AbsCollectionBuilder):
    """HathiLimitedViewBuilder."""

    BIB_ID_REGEX = r"([0-9]*)(v[0-9]*)?(m[0-9])?(i[0-9]*)?(_[0-9]*(i[0-9])?)?"
    METS_FILE_REGEX = r"\.mets\.xml"
    ZIP_FILE_REGEX = r"\.zip"
    PREFIX_REGEX = "UIUC|uiuc"
    package_matcher = re.compile(rf"^({PREFIX_REGEX})\.{BIB_ID_REGEX}$")
    zip_file_matcher = re.compile(rf"^{BIB_ID_REGEX}({ZIP_FILE_REGEX})$")
    mets_file_matcher = re.compile(rf"^{BIB_ID_REGEX}({METS_FILE_REGEX})$")

    @classmethod
    def is_package_dir_name(cls, dirname: str) -> bool:
        """Check if package matches directory naming convention."""
        return bool(cls.package_matcher.match(dirname))

    def build_batch(self, root: str):
        """Build batch."""
        others = []
        for item in os.scandir(root):

            if not item.is_dir() or not self.is_package_dir_name(item.name):
                others.append((item.path, item.is_dir()))
                continue

            new_package = Package(root)

            new_package.component_metadata[Metadata.ID] = \
                item.name.split(".")[-1]

            new_package.component_metadata[Metadata.PATH] = item.path
            new_package.component_metadata[Metadata.ITEM_NAME] = item.name
            self.build_package(parent=new_package, path=item.path)
            yield new_package

    def build_instance(self, parent, path: str, *args, **kwargs) -> None:
        file_category = kwargs['file_category']

        file_name = kwargs.get('filename')
        files = []
        if file_name is not None:
            files.append(file_name)

        new_instantiation = Instantiation(category=file_category,
                                          parent=parent,
                                          files=files)
        new_instantiation.sidecar_files = [
            os.path.split(sidecar_file)[-1] for sidecar_file in
            kwargs.get('sidecar_files', [])
        ]

        new_instantiation.component_metadata[Metadata.PATH] = path
        new_instantiation.component_metadata[Metadata.ID] = \
            os.path.splitext(file_name)[0]

    @classmethod
    def split_package_content(cls, item: "os.DirEntry[str]") -> \
            Tuple[
                Optional["os.DirEntry[str]"],
                Optional["os.DirEntry[str]"],
                Optional["os.DirEntry[str]"]
            ]:

        if cls.mets_file_matcher.match(item.name):
            return None, item, None

        if cls.zip_file_matcher.match(item.name):
            return item, None, None

        return None, None, item

    @staticmethod
    def filter_image_format(file_name: str) -> bool:
        valid_images_extension = [
            ".tif",
            ".jp2"
        ]
        ext = os.path.splitext(file_name)[1]
        return ext.lower() in valid_images_extension

    def build_package(self, parent, path: str, *args, **kwargs) -> None:
        package_builder = HathiLimitedViewPackageBuilder(path=path)
        zip_files, mets_files, invalid_files = package_builder.get_content()

        if len(zip_files) != 1:
            raise AssertionError(f"Expected {path} to have 1 zip file, "
                                 f"found {len(zip_files)}")

        if len(mets_files) != 1:
            raise AssertionError(f"Expected {path} to have 1 mets.xml file, "
                                 f"found {len(mets_files)}")
        if len(invalid_files) != 0:
            print(
                "Found invalid files {}".format(
                    ",".join(file.path for file in invalid_files)
                )
            )

        contents = self.get_zip_content(package_builder, zip_files)

        for k, files in contents['item'].items():
            self.build_item(parent, path=zip_files[0].path, item_name=k,
                            files=files)

    @classmethod
    def get_zip_content(cls, package_builder, zip_files):
        contents = {}

        for i in itertools.groupby(sorted(
                package_builder.iter_items_from_archive(zip_files[0]),
                key=package_builder.get_item_type),
                key=package_builder.get_item_type):
            files = i[1]
            contents[i[0]] = dict(files)
        return contents

    # pylint: disable=unused-argument
    def build_item(self, parent, *args, **kwargs) -> None:
        """Build item and add to parent.

        Args:
            parent:
            *args:
            **kwargs:

        """
        path_name = kwargs.get("path")
        new_item = Item(parent)
        new_item.component_metadata[Metadata.PATH] = path_name

        item_name = kwargs.get('item_name')
        if item_name is not None:
            new_item.component_metadata[Metadata.ITEM_NAME] = item_name

        file_types = {
            file_category: list(files)
            for file_category, files in itertools.groupby(
                sorted(
                    kwargs['files'],
                    key=lambda x: self.get_file_type(x).value
                ),
                key=self.get_file_type,
            )
        }

        for archived_file in itertools.chain(
                file_types.get(InstantiationTypes.ACCESS, []),
                file_types.get(InstantiationTypes.PRESERVATION, []),
                file_types.get(InstantiationTypes.SUPPLEMENTARY, [])):

            path, file_name = os.path.split(archived_file)
            self.build_instance(
                parent=new_item,
                path=path,
                filename=file_name,
                file_category=self.get_file_type(archived_file)
            )

    @classmethod
    def get_file_type(cls, file_name: str) -> InstantiationTypes:
        ext = os.path.splitext(file_name)[1]

        if cls.filter_image_format(file_name):
            if ext.lower() == ".tif":
                return InstantiationTypes.PRESERVATION
            if ext.lower() == ".jp2":
                return InstantiationTypes.ACCESS

        if ext.lower() == ".txt":
            return InstantiationTypes.SUPPLEMENTARY

        return InstantiationTypes.UNKNOWN


class HathiLimitedViewPackageBuilder:
    """HathiLimitedViewPackageBuilder."""

    BIB_ID_REGEX = r"([0-9]*)(v[0-9]*)?(m[0-9])?(i[0-9]*)?(_[0-9]*(i[0-9])?)?"
    METS_FILE_REGEX = r"\.mets\.xml"
    ZIP_FILE_REGEX = r"\.zip"
    PREFIX_REGEX = "UIUC|uiuc"

    package_matcher = re.compile(rf"^({PREFIX_REGEX})\.{BIB_ID_REGEX}$")
    zip_file_matcher = re.compile(f"^{BIB_ID_REGEX}({ZIP_FILE_REGEX})$")
    mets_file_matcher = re.compile(f"^{BIB_ID_REGEX}({METS_FILE_REGEX})$")

    def __init__(self, path: str) -> None:
        """HathiLimitedViewPackageBuilder.

        Args:
            path: Path that the package is located in
        """
        self.path = path

    @classmethod
    def split_package_content(cls, item: "os.DirEntry[str]") -> \
            Tuple[
                Optional["os.DirEntry[str]"],
                Optional["os.DirEntry[str]"],
                Optional["os.DirEntry[str]"]
            ]:

        if cls.mets_file_matcher.match(item.name):
            return None, item, None

        if cls.zip_file_matcher.match(item.name):
            return item, None, None

        return None, None, item

    @staticmethod
    def get_item_key(file_name: str) -> str:
        """Get hashable key for a filename.

        This is mainly used for sorting or grouping

        Args:
            file_name: file name to get a key for

        Returns: key for the file
        """
        return os.path.splitext(os.path.split(file_name)[-1])[0]

    @staticmethod
    def filter_files_only(
            zip_file_source: zipfile.ZipFile,
            file_name: str
    ) -> bool:

        return not zip_file_source.getinfo(file_name).is_dir()

    @classmethod
    def get_item_type(cls, item_group: Tuple[str, List[str]]) -> str:
        _, files = item_group
        for file in files:
            if cls.is_image_format(file) is True:
                return "item"
            if file.endswith("mets.xml") is True:
                return "metadata"
        return "unknown"

    @staticmethod
    def is_image_format(file_name: str) -> bool:
        valid_images_extension = [
            ".tif",
            ".jp2"
        ]
        ext = os.path.splitext(file_name)[1]
        return ext in valid_images_extension

    @classmethod
    def iter_items_from_archive(cls, zip_file: str) -> \
            Iterator[Tuple[str, Iterable[str]]]:

        with zipfile.ZipFile(zip_file) as item_contents:
            for file_group in itertools.groupby(
                    sorted(
                        filter(
                            lambda x: cls.filter_files_only(item_contents, x),
                            item_contents.namelist()
                        ),
                        key=cls.get_item_key),
                    cls.get_item_key):
                files = list(file_group[1])
                yield file_group[0], list(files)

    def get_content(self) -> Tuple[
        List["os.DirEntry[str]"],
        List["os.DirEntry[str]"],
        List["os.DirEntry[str]"]
    ]:
        zip_files: List["os.DirEntry[str]"] = []
        mets_files = []
        unidentified_files = []

        for item in os.scandir(self.path):
            zip_file, mets_file, unidentified_file = \
                self.split_package_content(item)

            if zip_file is not None:
                zip_files.append(zip_file)

            if mets_file is not None:
                mets_files.append(mets_file)
            if unidentified_file is not None:
                unidentified_files.append(unidentified_file)

        return zip_files, mets_files, unidentified_files
