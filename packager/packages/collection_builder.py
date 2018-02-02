import abc
import logging
import os
import typing
import warnings
import collections

from .collection import Instantiation, Item, Package, PackageObject
from . import collection


def _build_ds_instance(item, name, path):
    new_instantiation = Instantiation(category="access", parent=item)
    for file in filter(lambda i: i.is_file(), os.scandir(path)):
        if os.path.splitext(os.path.basename(file))[0] == name:
            new_instantiation.files.append(file.path)


def _build_ds_items(package, path):
    logger = logging.getLogger(__name__)
    files = sorted(set(map(lambda item: os.path.splitext(item)[0], os.listdir(path))))
    for unique_item in files:
        logger.debug(unique_item)
        new_item = Item(parent=package)
        new_item.component_metadata["item_name"] = unique_item
        _build_ds_instance(new_item, name=unique_item, path=path)


def _build_ds_object(parent_batch, path):
    for folder in filter(lambda i: i.is_dir(), os.scandir(path)):
        new_package = PackageObject(parent=parent_batch)
        new_package.component_metadata["path"] = folder.path
        new_package.component_metadata["id"] = folder.name
        new_package.component_metadata["title_page"] = None
        _build_ds_items(new_package, path=folder.path)


def build_ds_batch(root):
    new_batch = Package(root)
    new_batch.component_metadata["path"] = root
    new_batch.component_metadata["package_type"] = "DS HathiTrust Submission Package"
    _build_ds_object(parent_batch=new_batch, path=root)
    return new_batch


def build_bb_instance(new_item, path, name):
    new_instantiation = Instantiation(category="access", parent=new_item)
    for file in filter(lambda i: i.is_file(), os.scandir(path)):
        if os.path.splitext(os.path.basename(file))[0] == name:
            new_instantiation.files.append(file.path)


def build_bb_package(new_package, path):
    logger = logging.getLogger(__name__)
    files = set(map(lambda item: os.path.splitext(item)[0], os.listdir(path)))
    for unique_item in sorted(files):
        logger.debug(unique_item)
        new_item = Item(parent=new_package)
        new_item.component_metadata["item_name"] = unique_item
        build_bb_instance(new_item, name=unique_item, path=path)


def build_bb_batch(root) -> Package:
    logger = logging.getLogger(__name__)
    new_batch = Package(root)
    for directory in filter(lambda i: i.is_dir(), os.scandir(root)):
        logger.debug("scanning {}".format(directory.path))
        new_object = PackageObject(parent=new_batch)
        new_object.component_metadata['path'] = directory.path
        new_object.component_metadata["id"] = directory.name
        new_object.component_metadata["package_type"] = "Brittle Books HathiTrust Submission Package"
        build_bb_package(new_object, path=directory.path)
    return new_batch


def build_capture_one_instance(new_item, name, path):
    new_instantiation = Instantiation(category="unknown", parent=new_item)
    group_id = new_item.metadata["id"]

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

    for file in filter(is_it_an_instance, os.scandir(path)):
        new_instantiation.files.append(file.path)


def build_capture_one_package(new_package, path):
    packages_group_id = new_package.metadata['id']

    def get_group_items(item: os.DirEntry):
        file_item_group, _ = item.name.split("_")

        if file_item_group != packages_group_id:
            return False

        return True

    for file_ in filter(get_group_items, filter(lambda i: i.is_file(), os.scandir(path))):
        group_part, item_part = file_.name.split("_")
        item_part, _ = os.path.splitext(item_part)
        new_item = Item(parent=new_package)
        new_item.component_metadata["item_name"] = item_part
        build_capture_one_instance(new_item, name=item_part, path=path)


def build_capture_one_batch(root) -> Package:
    new_batch = Package(root)
    new_batch.component_metadata["path"] = root
    files = []

    for file_ in filter(lambda i: i.is_file(), os.scandir(root)):
        files.append(file_)

    files.sort(key=lambda f: f.name)

    group_ids = set()

    for file_ in files:
        group_id, _ = file_.name.split("_")
        group_ids.add(group_id)

    for object_name in sorted(group_ids):
        new_object = PackageObject(parent=new_batch)
        new_object.component_metadata['id'] = object_name
        new_object.component_metadata['package_type'] = "Capture One Package"
        build_capture_one_package(new_object, path=root)

    return new_batch


def build_hathi_tiff_instance(new_item, filename, path):
    new_instantiation = Instantiation(category="access", parent=new_item)

    def is_it_an_instance(item: os.DirEntry):
        if not item.is_file():
            return False

        filename_, ext = os.path.splitext(item.name)
        if ext.lower() != ".tif":
            return False

        if filename_ != filename:
            return False

        return True

    for file_ in filter(is_it_an_instance, os.scandir(path)):
        new_instantiation.files.append(file_.path)


def build_hathi_tiff_package(new_object, path):
    for file_ in filter(lambda i: i.is_file(), os.scandir(path)):
        new_item = Item(parent=new_object)
        item_part, _ = os.path.splitext(file_.name)
        new_item.component_metadata["item_name"] = item_part
        build_hathi_tiff_instance(new_item, filename=item_part, path=path)


def build_hathi_tiff_batch(root):
    new_batch = Package(root)
    new_batch.component_metadata["path"] = root

    # directories = []
    objects = []

    for dir_ in filter(lambda i: i.is_dir(), os.scandir(root)):
        new_object = PackageObject(parent=new_batch)
        new_object.component_metadata['id'] = dir_.name
        new_object.metadata['path'] = dir_.path
        new_object.component_metadata['package_type'] = "HathiTrust Tiff"
        build_hathi_tiff_package(new_object, path=dir_.path)
        # new_object.metadata


    return new_batch