"""Package generated from the lab using Capture One."""

# pylint: disable=unsubscriptable-object
from __future__ import annotations

import logging
import os
from typing import Optional, Dict, Callable, Iterator
from uiucprescon.packager import transformations
from uiucprescon.packager.common import \
    Metadata, PackageTypes, InstantiationTypes
from uiucprescon.packager.packages import collection_builder, collection
from .abs_package_builder import AbsPackageBuilder


class CaptureOneBuilder(collection_builder.AbsCollectionBuilder):
    """CaptureOneBuilder.

    .. versionadded:: 0.2.11
        Identifying the components of the filename can be done modified by
        adding a function to the splitter property
    """

    def __init__(self) -> None:
        super().__init__()
        self.splitter: \
            Optional[Callable[[str], Optional[Dict[str, str]]]] = None

    def identify_file_name_parts(self,
                                 file_name: str) -> Optional[Dict[str, str]]:
        """Identify the components that make up the file name.

        Args:
            file_name: the name of a given file

        Returns:
            Dictionary of all the identified components in the file

        """

        if self.splitter is not None:
            # pylint: disable=not-callable
            # This is a callable via dependency injection by assigning splitter
            #   to a function.
            return self.splitter(file_name)
        return collection_builder.underscore_splitter(file_name)

    def build_batch(self, root: str) -> collection_builder.AbsPackageComponent:
        new_batch = collection.Package(root)
        new_batch.component_metadata[Metadata.PATH] = root
        files = []

        def filter_only_tiff(item: "os.DirEntry[str]") -> bool:
            return item.name.lower().endswith(".tif")

        for file_ in filter(
                filter_only_tiff,
                filter(
                    self.filter_nonsystem_files_only,
                    os.scandir(root)
                )):
            files.append(file_)

        files.sort(key=lambda f: f.name)

        group_ids = set()

        for file_ in files:
            try:
                file_name_parts = self.identify_file_name_parts(file_.name)
                if file_name_parts is None:
                    raise ValueError(
                        f"File {file_.name} doesn't match expected pattern"
                    )

                group_id = file_name_parts['group']
                group_ids.add(group_id)
            except ValueError:
                raise ValueError(
                    "Unable to split {}".format(file_.name))

        for object_name in sorted(group_ids):
            new_object = collection.PackageObject(parent=new_batch)
            new_object.component_metadata[Metadata.ID] = object_name

            new_object.component_metadata[Metadata.PACKAGE_TYPE] = \
                PackageTypes.CAPTURE_ONE_SESSION
            self.build_package(new_object, root)
        return new_batch

    def build_instance(
            self,
            parent,
            path: str,
            filename: str,
            *args,
            **kwargs
    ) -> None:

        group_id = parent.metadata[Metadata.ID]

        def is_it_an_instance(item: "os.DirEntry[str]") -> bool:
            if not item.is_file():
                return False
            file_name_parts = self.identify_file_name_parts(item.name)
            if file_name_parts is None:
                raise ValueError(
                    "File does not match expected naming pattern {}".format(
                        item.path)
                )
            item_group = file_name_parts['group']
            item_inst = file_name_parts['part']
            if item_inst != filename:
                return False

            if item_group != group_id:
                return False
            return True

        files = []
        for file in filter(is_it_an_instance,
                           filter(self.filter_nonsystem_files_only,
                                  os.scandir(path))):
            if not file.name.lower().endswith(".tif"):
                continue

            files.append(file.path)

        collection.Instantiation(
            category=InstantiationTypes.PRESERVATION,
            parent=parent,
            files=files)

    def build_package(self, parent, path: str, *args, **kwargs) -> None:
        group_id = parent.metadata[Metadata.ID]

        non_system_files = \
            filter(self.filter_nonsystem_files_only, os.scandir(path))

        def filter_by_group(candidate_file: "os.DirEntry[str]") -> bool:
            parts = self.identify_file_name_parts(candidate_file.name)
            return parts is not None and parts['group'] == group_id

        for file_ in filter(filter_by_group, non_system_files):
            file_name_parts = self.identify_file_name_parts(file_.name)
            if file_name_parts is None:
                raise ValueError(
                    "File does not match expected naming pattern {}".format(
                        file_.path)
                )
            if file_name_parts['extension'].lower() != ".tif":
                continue
            item_part = file_name_parts['part']
            new_item = collection.Item(parent=parent)
            new_item.component_metadata[Metadata.ITEM_NAME] = item_part
            self.build_instance(new_item, path, item_part)


class CaptureOnePackage(AbsPackageBuilder):
    """Package generated from the lab using Capture One.

    This package generator splits filename using a delimiter that defaults to
    an underscore.

    + batch folder
        - uniqueID1_00000001.tif
        - uniqueID1_00000002.tif
        - uniqueID1_00000003.tif
        - uniqueID2_00000001.tif
        - uniqueID2_00000002.tif
    """

    delimiter_splitters: Dict[str,
                              Callable[[str], Optional[Dict[str, str]]]] = {
        '_': collection_builder.underscore_splitter,
        '-': collection_builder.dash_splitter
    }

    def __init__(self, delimiter: str = "_") -> None:
        """Generate a new package factory.

        Args:
            delimiter: the character uses to separate the text of the filename
                to identify the part and group the file belongs to.

                Defaults to an underscore.
        """
        self.delimiter = delimiter
        splitter = CaptureOnePackage.delimiter_splitters.get(delimiter)
        if splitter is None:
            def splitter(filename: str) -> Optional[Dict[str, str]]:
                return collection_builder.delimiter_splitter(
                    file_name=filename,
                    delimiter=delimiter
                )

        self.package_builder = CaptureOneBuilder()
        self.package_builder.splitter = splitter

    def locate_packages(self, path: str) -> Iterator[collection.Package]:

        yield from self.package_builder.build_batch(path)

    def transform(self, package: collection.Package, dest: str) -> None:
        logger = logging.getLogger(__name__)
        logger.setLevel(AbsPackageBuilder.log_level)

        for item in package:
            item_name = item.metadata[Metadata.ITEM_NAME]
            object_name = item.metadata[Metadata.ID]
            for inst in item:
                files = list(inst.get_files())
                if len(files) != 1:
                    raise AssertionError("More than one file found")

                for file_ in files:
                    _, ext = os.path.splitext(file_)
                    new_file_name = \
                        f"{object_name}{self.delimiter}{item_name}{ext}"

                    copy = transformations.Transformers(
                        strategy=transformations.CopyFile(),
                        logger=logger
                    )
                    new_file_path = os.path.join(dest, new_file_name)
                    copy.transform(source=file_, destination=new_file_path)
