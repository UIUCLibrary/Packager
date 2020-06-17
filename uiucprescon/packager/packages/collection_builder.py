import abc
import itertools
import logging
import os
import warnings

from .collection import Instantiation, Item, Package, PackageObject
from uiucprescon.packager.common import Metadata, PackageTypes
from uiucprescon.packager.common import InstantiationTypes


def _build_ds_instance(item, name, path):
    warnings.warn("Use DSBuilder.build_instance instead",
                  PendingDeprecationWarning)

    new_instantiation = Instantiation(category=InstantiationTypes.ACCESS,
                                      parent=item)

    for file in filter(lambda i: i.is_file(), os.scandir(path)):
        if os.path.splitext(os.path.basename(file))[0] == name:
            new_instantiation.files.append(file.path)


def _build_ds_items(package, path):
    logger = logging.getLogger(__name__)

    files = sorted(set(
        map(lambda item: os.path.splitext(item)[0], os.listdir(path)))
    )

    for unique_item in files:
        logger.debug(unique_item)
        new_item = Item(parent=package)
        new_item.component_metadata[Metadata.ITEM_NAME] = unique_item
        _build_ds_instance(new_item, name=unique_item, path=path)


def _build_ds_object(parent_batch, path):
    warnings.warn("Use DSBuilder.build_package instead",
                  PendingDeprecationWarning)
    for folder in filter(lambda i: i.is_dir(), os.scandir(path)):
        new_package = PackageObject(parent=parent_batch)
        new_package.component_metadata[Metadata.PATH] = folder.path
        new_package.component_metadata[Metadata.ID] = folder.name
        new_package.component_metadata[Metadata.TITLE_PAGE] = None
        _build_ds_items(new_package, path=folder.path)


def build_ds_batch(root):

    warnings.warn("Use DSBuilder.build_batch instead ",
                  PendingDeprecationWarning)

    new_batch = Package(root)
    new_batch.component_metadata[Metadata.PATH] = root

    new_batch.component_metadata[Metadata.PACKAGE_TYPE] = \
        PackageTypes.DS_HATHI_TRUST_SUBMISSION

    _build_ds_object(parent_batch=new_batch, path=root)
    return new_batch


def build_bb_instance(new_item, path, name):
    warnings.warn("Use BrittleBooksBuilder.build_instance instead ",
                  PendingDeprecationWarning)
    new_instantiation = Instantiation(category=InstantiationTypes.ACCESS,
                                      parent=new_item)

    for file in filter(lambda i: i.is_file(), os.scandir(path)):
        if os.path.splitext(os.path.basename(file))[0] == name:
            new_instantiation.files.append(file.path)


def build_bb_package(new_package, path):
    warnings.warn("Use BrittleBooksBuilder.build_package instead ",
                  PendingDeprecationWarning)
    logger = logging.getLogger(__name__)
    files = set(map(lambda item: os.path.splitext(item)[0], os.listdir(path)))
    for unique_item in sorted(files):
        logger.debug(unique_item)
        new_item = Item(parent=new_package)
        new_item.component_metadata[Metadata.ITEM_NAME] = unique_item
        build_bb_instance(new_item, name=unique_item, path=path)


def build_bb_batch(root) -> Package:

    warnings.warn("Use BrittleBooksBuilder.build_batch instead ",
                  PendingDeprecationWarning)

    logger = logging.getLogger(__name__)
    new_batch = Package(root)
    for directory in filter(lambda i: i.is_dir(), os.scandir(root)):
        logger.debug("scanning {}".format(directory.path))
        new_object = PackageObject(parent=new_batch)
        new_object.component_metadata[Metadata.PATH] = directory.path
        new_object.component_metadata[Metadata.ID] = directory.name

        new_object.component_metadata[Metadata.PACKAGE_TYPE] = \
            PackageTypes.BRITTLE_BOOKS_HATHI_TRUST_SUBMISSION

        build_bb_package(new_object, path=directory.path)
    return new_batch


class AbsCollectionBuilder(metaclass=abc.ABCMeta):
    @classmethod
    @abc.abstractmethod
    def build_batch(cls, root):
        """Build a new batch of a given packaging type"""

    @classmethod
    @abc.abstractmethod
    def build_instance(cls, parent, path, filename):
        pass

    @classmethod
    @abc.abstractmethod
    def build_package(cls, parent, path):
        pass

    @staticmethod
    def filter_same_name_files(item: os.DirEntry, filename):

        if not item.is_file():
            return False

        base, _ = os.path.splitext(item.name)

        if base != filename:
            return False
        return True

    @staticmethod
    def filter_nonsystem_files_only(item: os.DirEntry) -> bool:
        system_files = [
            "Thumbs.db",
            "desktop.ini",
            ".DS_Store"
        ]

        if not item.is_file():
            return False
        if item.name in system_files:
            return False
        return True


class DSBuilder(AbsCollectionBuilder):

    @classmethod
    def build_batch(cls, root):
        new_batch = Package(root)
        new_batch.component_metadata[Metadata.PATH] = root

        new_batch.component_metadata[Metadata.PACKAGE_TYPE] = \
            PackageTypes.DS_HATHI_TRUST_SUBMISSION

        cls.build_package(parent=new_batch, path=root)
        return new_batch

    @classmethod
    def build_instance(cls, parent, path, filename):

        new_instantiation = Instantiation(category=InstantiationTypes.ACCESS,
                                          parent=parent)

        for file in filter(lambda i: i.is_file(), os.scandir(path)):
            if os.path.splitext(os.path.basename(file))[0] == filename:
                new_instantiation.files.append(file.path)

    @classmethod
    def build_package(cls, parent, path):
        for folder in filter(lambda i: i.is_dir(), os.scandir(path)):
            new_package = PackageObject(parent=parent)
            new_package.component_metadata[Metadata.PATH] = folder.path
            new_package.component_metadata[Metadata.ID] = folder.name
            new_package.component_metadata[Metadata.TITLE_PAGE] = None
            cls._build_ds_items(new_package, path=folder.path)

    @classmethod
    def _build_ds_items(cls, parent, path):
        logger = logging.getLogger(__name__)

        files = sorted(set(
            map(lambda item: os.path.splitext(item)[0], os.listdir(path)))
        )

        for unique_item in files:
            logger.debug(unique_item)
            new_item = Item(parent=parent)
            new_item.component_metadata[Metadata.ITEM_NAME] = unique_item
            cls.build_instance(new_item, filename=unique_item, path=path)


class BrittleBooksBuilder(AbsCollectionBuilder):

    @classmethod
    def build_instance(cls, parent, path, filename):
        new_instantiation = Instantiation(
            category=InstantiationTypes.ACCESS,
            parent=parent)

        for file in filter(lambda i: i.is_file(), os.scandir(path)):
            if os.path.splitext(os.path.basename(file))[0] == filename:
                new_instantiation.files.append(file.path)

    @classmethod
    def build_package(cls, parent, path):
        logger = logging.getLogger(__name__)

        files = set(
            map(lambda item: os.path.splitext(item)[0], os.listdir(path)))

        for unique_item in sorted(files):
            logger.debug(unique_item)
            new_item = Item(parent=parent)
            new_item.component_metadata[Metadata.ITEM_NAME] = unique_item
            cls.build_instance(new_item, filename=unique_item, path=path)

    @classmethod
    def build_batch(cls, root):
        logger = logging.getLogger(__name__)
        new_batch = Package(root)
        for directory in filter(lambda i: i.is_dir(), os.scandir(root)):
            logger.debug("scanning {}".format(directory.path))
            new_object = PackageObject(parent=new_batch)
            new_object.component_metadata[Metadata.PATH] = directory.path
            new_object.component_metadata[Metadata.ID] = directory.name

            new_object.component_metadata[Metadata.PACKAGE_TYPE] = \
                PackageTypes.BRITTLE_BOOKS_HATHI_TRUST_SUBMISSION

            cls.build_package(new_object, path=directory.path)
        return new_batch


class CaptureOneBuilder(AbsCollectionBuilder):

    @classmethod
    def build_batch(cls, root):
        new_batch = Package(root)
        new_batch.component_metadata[Metadata.PATH] = root
        files = []

        for file_ in filter(cls.filter_nonsystem_files_only, os.scandir(root)):
            files.append(file_)

        files.sort(key=lambda f: f.name)

        group_ids = set()

        for file_ in files:
            try:
                group_id, _ = file_.name.split("_")
                group_ids.add(group_id)
            except ValueError:
                raise ValueError(
                    "Unable to split {} with underscore".format(file_.name))

        for object_name in sorted(group_ids):
            new_object = PackageObject(parent=new_batch)
            new_object.component_metadata[Metadata.ID] = object_name

            new_object.component_metadata[Metadata.PACKAGE_TYPE] = \
                PackageTypes.CAPTURE_ONE_SESSION
            cls.build_package(new_object, root)
        return new_batch

    @classmethod
    def build_instance(cls, parent, path, filename):

        new_instantiation = \
            Instantiation(category=InstantiationTypes.PRESERVATION,
                          parent=parent)

        group_id = parent.metadata[Metadata.ID]

        def is_it_an_instance(item: os.DirEntry):
            if not item.is_file():
                return False

            item_group, item_inst = item.name.split("_")
            item_inst, _ = os.path.splitext(item_inst)
            if item_inst != filename:
                return False

            if item_group != group_id:
                return False
            return True

        for file in filter(is_it_an_instance,
                           filter(cls.filter_nonsystem_files_only,
                                  os.scandir(path))):

            new_instantiation.files.append(file.path)

    @staticmethod
    def get_group_items(item: os.DirEntry, packages_group_id):
        file_item_group, _ = item.name.split("_")

        if file_item_group != packages_group_id:
            return False

        return True

    @classmethod
    def build_package(cls, parent, path):
        group_id = parent.metadata[Metadata.ID]

        non_system_files = \
            filter(cls.filter_nonsystem_files_only, os.scandir(path))

        for file_ in filter(lambda x, group_id=group_id:
                            cls.get_group_items(x, group_id),
                            non_system_files):

            group_part, item_part = file_.name.split("_")
            item_part, _ = os.path.splitext(item_part)
            new_item = Item(parent=parent)
            new_item.component_metadata[Metadata.ITEM_NAME] = item_part
            cls.build_instance(new_item, path, item_part)


class HathiTiffBuilder(AbsCollectionBuilder):

    @classmethod
    def build_batch(cls, root):
        new_batch = Package(root)
        new_batch.component_metadata[Metadata.PATH] = root

        for dir_ in filter(lambda i: i.is_dir(), os.scandir(root)):
            new_object = PackageObject(parent=new_batch)
            new_object.component_metadata[Metadata.ID] = dir_.name
            new_object.component_metadata[Metadata.PATH] = dir_.path

            new_object.component_metadata[Metadata.PACKAGE_TYPE] = \
                PackageTypes.HATHI_TRUST_TIFF_SUBMISSION
            cls.build_package(new_object, path=dir_.path)

        return new_batch

    @staticmethod
    def filter_tiff_files(item: os.DirEntry) -> bool:
        if not item.is_file():
            return False

        base, ext = os.path.splitext(item.name)
        if ext.lower() != ".tif":
            return False
        return True

    @classmethod
    def build_package(cls, parent, path):

        for file_ in filter(cls.filter_tiff_files, os.scandir(path)):
            new_item = Item(parent=parent)
            item_part, _ = os.path.splitext(file_.name)
            new_item.component_metadata[Metadata.ITEM_NAME] = item_part
            cls.build_instance(new_item, filename=item_part, path=path)

    @classmethod
    def build_instance(cls, parent, path, filename):

        new_instantiation = Instantiation(category=InstantiationTypes.ACCESS,
                                          parent=parent)

        def _organize_files(item: os.DirEntry) -> str:
            base, ext = os.path.splitext(item.name)
            if ext.lower() == ".tif":
                return "main_files"
            else:
                return "sidecar"

        matching_files = \
            filter(lambda x, file_name=filename:
                   cls.filter_same_name_files(x, file_name), os.scandir(path))

        sidecar_files = []
        main_files = []
        for k, v in itertools.groupby(matching_files, key=_organize_files):
            if k == "sidecar":
                for file_ in v:
                    sidecar_files.append(file_)
            elif k == "main_files":
                for file_ in v:
                    main_files.append(file_)

        for file_ in main_files:
            new_instantiation.files.append(file_.path)

        for file_ in sidecar_files:
            new_instantiation.sidecar_files.append(file_.path)


class DigitalLibraryCompoundBuilder(AbsCollectionBuilder):

    @classmethod
    def build_batch(cls, root):

        new_batch = Package(root)
        new_batch.component_metadata[Metadata.PATH] = root

        for dir_ in filter(lambda i: i.is_dir(), os.scandir(root)):
            new_object = PackageObject(parent=new_batch)
            new_object.component_metadata[Metadata.ID] = dir_.name
            new_object.metadata[Metadata.PATH] = dir_.path

            new_object.component_metadata[Metadata.PACKAGE_TYPE] = \
                PackageTypes.DIGITAL_LIBRARY_COMPOUND

            cls.build_package(new_object, path=dir_.path)
        return new_batch

    @classmethod
    def build_instance(cls, parent, filename, path):
        access_file = os.path.join(path, "access", filename + ".jp2")

        preservation_file = os.path.join(path, "preservation",
                                         filename + ".tif")

        if not os.path.exists(access_file):
            raise FileNotFoundError(f"Access file {access_file} not found")

        if not os.path.exists(preservation_file):
            raise FileNotFoundError(
                f"Preservation file {preservation_file} not found")

        access_instance = Instantiation(category=InstantiationTypes.ACCESS,
                                        parent=parent)

        access_instance.files.append(access_file)

        preservation_instance = Instantiation(
            category=InstantiationTypes.PRESERVATION, parent=parent)

        preservation_instance.files.append(preservation_file)

    @staticmethod
    def file_type_filter(item: os.DirEntry, file_extension) -> bool:
        if not item.is_file():
            return False
        _, ext = os.path.splitext(item.name)
        if ext.lower() != file_extension:
            return False
        return True

    @classmethod
    def build_package(cls, parent, path):
        access_path = os.path.join(path, "access")
        preservation_path = os.path.join(path, "preservation")

        if not os.path.exists(access_path):
            raise FileNotFoundError(f"Access path {access_path} not found")

        if not os.path.exists(preservation_path):
            raise FileNotFoundError(
                f"Preservation path {preservation_path} not found")

        access_files = sorted(
            filter(lambda i: cls.file_type_filter(i, ".jp2"),
                   os.scandir(access_path)),
            key=lambda f: f.name)

        preservation_files = sorted(
            filter(lambda i: cls.file_type_filter(i, ".tif"),
                   os.scandir(preservation_path)),
            key=lambda f: f.name)

        if len(access_files) != len(preservation_files):
            raise AssertionError("Number of access files do not match the "
                                 "number of preservation files")

        for access_file, preservation_file in \
                zip(access_files, preservation_files):

            assert os.path.splitext(access_file.name)[0] == \
                   os.path.splitext(preservation_file.name)[0]

            item_id = os.path.splitext(access_file.name)[0]
            new_item = Item(parent=parent)
            cls.build_instance(new_item, filename=item_id, path=path)


class HathiJp2Builder(AbsCollectionBuilder):
    @classmethod
    def build_batch(cls, root):

        new_batch = Package(root)
        new_batch.component_metadata[Metadata.PATH] = root

        for dir_ in filter(lambda i: i.is_dir(), os.scandir(root)):
            new_object = PackageObject(parent=new_batch)
            new_object.component_metadata[Metadata.ID] = dir_.name
            new_object.component_metadata[Metadata.PATH] = dir_.path

            new_object.component_metadata[Metadata.PACKAGE_TYPE] = \
                PackageTypes.HATHI_TRUST_JP2_SUBMISSION

            cls.build_package(new_object, path=dir_.path)

        return new_batch

    @staticmethod
    def filter_tiff_files(item: os.DirEntry) -> bool:
        if not item.is_file():
            return False

        base, ext = os.path.splitext(item.name)
        if ext.lower() != ".jp2":
            return False
        return True

    @classmethod
    def build_package(cls, parent, path):
        for file_ in filter(cls.filter_tiff_files, os.scandir(path)):
            new_item = Item(parent=parent)
            item_part, _ = os.path.splitext(file_.name)
            new_item.component_metadata[Metadata.ITEM_NAME] = item_part
            cls.build_instance(new_item, filename=item_part, path=path)

    @staticmethod
    def _organize_files(item: os.DirEntry) -> str:
        base, ext = os.path.splitext(item.name)
        if ext.lower() == ".jp2":
            return "main_files"
        else:
            return "sidecar"

    @classmethod
    def build_instance(cls, parent, filename, path):
        new_instantiation = Instantiation(category=InstantiationTypes.ACCESS,
                                          parent=parent)

        matching_files = \
            filter(lambda x, file_name=filename:
                   cls.filter_same_name_files(x, file_name), os.scandir(path))

        sidecar_files = []

        main_files = []
        for k, v in itertools.groupby(matching_files, key=cls._organize_files):
            if k == "sidecar":
                for file_ in v:
                    sidecar_files.append(file_)
            elif k == "main_files":
                for file_ in v:
                    main_files.append(file_)

        for file_ in main_files:
            new_instantiation.files.append(file_.path)

        for file_ in sidecar_files:
            new_instantiation.sidecar_files.append(file_.path)
