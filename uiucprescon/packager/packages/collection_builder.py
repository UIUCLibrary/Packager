import itertools
import logging
import os

from .collection import Instantiation, Item, Package, PackageObject
from uiucprescon.packager.common import Metadata, PackageTypes
from uiucprescon.packager.common import InstantiationTypes


def _build_ds_instance(item, name, path):

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
    for folder in filter(lambda i: i.is_dir(), os.scandir(path)):
        new_package = PackageObject(parent=parent_batch)
        new_package.component_metadata[Metadata.PATH] = folder.path
        new_package.component_metadata[Metadata.ID] = folder.name
        new_package.component_metadata[Metadata.TITLE_PAGE] = None
        _build_ds_items(new_package, path=folder.path)


def build_ds_batch(root):
    new_batch = Package(root)
    new_batch.component_metadata[Metadata.PATH] = root

    new_batch.component_metadata[Metadata.PACKAGE_TYPE] = \
        PackageTypes.DS_HATHI_TRUST_SUBMISSION

    _build_ds_object(parent_batch=new_batch, path=root)
    return new_batch


def build_bb_instance(new_item, path, name):

    new_instantiation = Instantiation(category=InstantiationTypes.ACCESS,
                                      parent=new_item)

    for file in filter(lambda i: i.is_file(), os.scandir(path)):
        if os.path.splitext(os.path.basename(file))[0] == name:
            new_instantiation.files.append(file.path)


def build_bb_package(new_package, path):
    logger = logging.getLogger(__name__)
    files = set(map(lambda item: os.path.splitext(item)[0], os.listdir(path)))
    for unique_item in sorted(files):
        logger.debug(unique_item)
        new_item = Item(parent=new_package)
        new_item.component_metadata[Metadata.ITEM_NAME] = unique_item
        build_bb_instance(new_item, name=unique_item, path=path)


def build_bb_batch(root) -> Package:
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


def build_capture_one_instance(new_item, name, path):

    new_instantiation = Instantiation(category=InstantiationTypes.PRESERVATION,
                                      parent=new_item)

    group_id = new_item.metadata[Metadata.ID]

    def is_it_an_instance(item: os.DirEntry):
        if not item.is_file():
            return False

        item_group, item_inst = item.name.split("_")
        item_inst, _ = os.path.splitext(item_inst)
        if item_inst != name:
            return False

        if item_group != group_id:
            return False
        return True

    for file in filter(is_it_an_instance,
                       filter(filter_none_system_files_only,
                              os.scandir(path))):

        new_instantiation.files.append(file.path)


def build_capture_one_package(new_package, path):
    packages_group_id = new_package.metadata[Metadata.ID]

    def get_group_items(item: os.DirEntry):
        file_item_group, _ = item.name.split("_")

        if file_item_group != packages_group_id:
            return False

        return True

    for file_ in filter(get_group_items, filter(filter_none_system_files_only,
                                                os.scandir(path))):

        group_part, item_part = file_.name.split("_")
        item_part, _ = os.path.splitext(item_part)
        new_item = Item(parent=new_package)
        new_item.component_metadata[Metadata.ITEM_NAME] = item_part
        build_capture_one_instance(new_item, name=item_part, path=path)


def filter_none_system_files_only(item: os.DirEntry):
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


def build_capture_one_batch(root) -> Package:
    new_batch = Package(root)
    new_batch.component_metadata[Metadata.PATH] = root
    files = []

    for file_ in filter(filter_none_system_files_only, os.scandir(root)):
        files.append(file_)

    files.sort(key=lambda f: f.name)

    group_ids = set()

    for file_ in files:
        group_id, _ = file_.name.split("_")
        group_ids.add(group_id)

    for object_name in sorted(group_ids):
        new_object = PackageObject(parent=new_batch)
        new_object.component_metadata[Metadata.ID] = object_name

        new_object.component_metadata[Metadata.PACKAGE_TYPE] = \
            PackageTypes.CAPTURE_ONE_SESSION

        build_capture_one_package(new_object, path=root)

    return new_batch


def build_hathi_tiff_instance(new_item, filename, path):

    new_instantiation = Instantiation(category=InstantiationTypes.ACCESS,
                                      parent=new_item)

    def filter_same_name_files(item: os.DirEntry):

        if not item.is_file():
            return False

        base, _ = os.path.splitext(item.name)

        if base != filename:
            return False
        return True

    def _organize_files(item: os.DirEntry) -> str:
        base, ext = os.path.splitext(item.name)
        if ext.lower() == ".tif":
            return "main_files"
        else:
            return "sidecar"

    matching_files = filter(filter_same_name_files, os.scandir(path))

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


def build_hathi_tiff_package(new_object, path):
    def filter_tiff_files(item: os.DirEntry) -> bool:
        if not item.is_file():
            return False

        base, ext = os.path.splitext(item.name)
        if ext.lower() != ".tif":
            return False
        return True

    for file_ in filter(filter_tiff_files, os.scandir(path)):
        new_item = Item(parent=new_object)
        item_part, _ = os.path.splitext(file_.name)
        new_item.component_metadata[Metadata.ITEM_NAME] = item_part
        build_hathi_tiff_instance(new_item, filename=item_part, path=path)


def build_hathi_tiff_batch(root):
    new_batch = Package(root)
    new_batch.component_metadata[Metadata.PATH] = root

    for dir_ in filter(lambda i: i.is_dir(), os.scandir(root)):
        new_object = PackageObject(parent=new_batch)
        new_object.component_metadata[Metadata.ID] = dir_.name
        new_object.component_metadata[Metadata.PATH] = dir_.path

        new_object.component_metadata[Metadata.PACKAGE_TYPE] = \
            PackageTypes.HATHI_TRUST_TIFF_SUBMISSION

        build_hathi_tiff_package(new_object, path=dir_.path)

    return new_batch


def build_digital_library_compound_item(new_item, path, item_name):
    access_file = os.path.join(path, "access", item_name + ".jp2")
    preservation_file = os.path.join(path, "preservation", item_name + ".tif")

    assert os.path.exists(access_file)
    assert os.path.exists(preservation_file)

    access_instance = Instantiation(category=InstantiationTypes.ACCESS,
                                    parent=new_item)

    access_instance.files.append(access_file)

    preservation_instance = Instantiation(
        category=InstantiationTypes.PRESERVATION, parent=new_item)

    preservation_instance.files.append(preservation_file)


def build_digital_library_compound_package(new_object, path):
    def file_type_filter(item: os.DirEntry, file_extension):
        if not item.is_file():
            return False
        _, ext = os.path.splitext(item.name)
        if ext.lower() != file_extension:
            return False

        return True

    access_path = os.path.join(path, "access")
    preservation_path = os.path.join(path, "preservation")

    assert os.path.exists(access_path)
    assert os.path.exists(preservation_path)

    access_files = sorted(
        filter(lambda i: file_type_filter(i, ".jp2"),
               os.scandir(access_path)),
        key=lambda f: f.name)

    preservation_files = sorted(
        filter(lambda i: file_type_filter(i, ".tif"),
               os.scandir(preservation_path)),
        key=lambda f: f.name)

    assert len(access_files) == len(preservation_files)

    for access_file, preservation_file in \
            zip(access_files, preservation_files):

        assert os.path.splitext(access_file.name)[0] == \
               os.path.splitext(preservation_file.name)[0]

        item_id = os.path.splitext(access_file.name)[0]
        new_item = Item(parent=new_object)

        build_digital_library_compound_item(new_item,
                                            path=path,
                                            item_name=item_id)


def build_digital_library_compound_batch(root):
    new_batch = Package(root)
    new_batch.component_metadata[Metadata.PATH] = root

    for dir_ in filter(lambda i: i.is_dir(), os.scandir(root)):
        new_object = PackageObject(parent=new_batch)
        new_object.component_metadata[Metadata.ID] = dir_.name
        new_object.metadata[Metadata.PATH] = dir_.path

        new_object.component_metadata[Metadata.PACKAGE_TYPE] = \
            PackageTypes.DIGITAL_LIBRARY_COMPOUND

        build_digital_library_compound_package(new_object, path=dir_.path)
    return new_batch


def build_hathi_jp2_batch(root):
    new_batch = Package(root)
    new_batch.component_metadata[Metadata.PATH] = root

    for dir_ in filter(lambda i: i.is_dir(), os.scandir(root)):
        new_object = PackageObject(parent=new_batch)
        new_object.component_metadata[Metadata.ID] = dir_.name
        new_object.component_metadata[Metadata.PATH] = dir_.path

        new_object.component_metadata[Metadata.PACKAGE_TYPE] = \
            PackageTypes.HATHI_TRUST_JP2_SUBMISSION

        build_hathi_jp2_package(new_object, path=dir_.path)

    return new_batch


def build_hathi_jp2_instance(new_item, filename, path):

    new_instantiation = Instantiation(category=InstantiationTypes.ACCESS,
                                      parent=new_item)

    def filter_same_name_files(item: os.DirEntry):

        if not item.is_file():
            return False

        base, _ = os.path.splitext(item.name)

        if base != filename:
            return False
        return True

    def _organize_files(item: os.DirEntry) -> str:
        base, ext = os.path.splitext(item.name)
        if ext.lower() == ".jp2":
            return "main_files"
        else:
            return "sidecar"

    matching_files = filter(filter_same_name_files, os.scandir(path))

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


def build_hathi_jp2_package(new_object, path):
    def filter_tiff_files(item: os.DirEntry) -> bool:
        if not item.is_file():
            return False

        base, ext = os.path.splitext(item.name)
        if ext.lower() != ".jp2":
            return False
        return True

    for file_ in filter(filter_tiff_files, os.scandir(path)):
        new_item = Item(parent=new_object)
        item_part, _ = os.path.splitext(file_.name)
        new_item.component_metadata[Metadata.ITEM_NAME] = item_part
        build_hathi_jp2_instance(new_item, filename=item_part, path=path)
