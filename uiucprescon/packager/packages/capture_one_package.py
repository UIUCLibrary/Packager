"""Package generated from the lab using Capture One."""

# pylint: disable=unsubscriptable-object

import logging
import os
from typing import Optional, Dict, Callable, Iterator
from uiucprescon.packager import transformations
from uiucprescon.packager.common import Metadata
from uiucprescon.packager.packages.collection import Package
from . import collection_builder
from .abs_package_builder import AbsPackageBuilder


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

        self.package_builder = collection_builder.CaptureOneBuilder()
        self.package_builder.splitter = splitter

    def locate_packages(self, path: str) -> Iterator[Package]:

        for package in self.package_builder.build_batch(path):
            yield package

    def transform(self, package: Package, dest: str) -> None:
        logger = logging.getLogger(__name__)
        logger.setLevel(AbsPackageBuilder.log_level)

        for item in package:
            item_name = item.metadata[Metadata.ITEM_NAME]
            object_name = item.metadata[Metadata.ID]
            for inst in item:
                if len(inst.files) != 1:
                    raise AssertionError("More than one file found")
                for file_ in inst.files:
                    _, ext = os.path.splitext(file_)
                    new_file_name = \
                        f"{object_name}{self.delimiter}{item_name}{ext}"

                    copy = transformations.Transformers(
                        strategy=transformations.CopyFile(),
                        logger=logger
                    )
                    new_file_path = os.path.join(dest, new_file_name)
                    copy.transform(source=file_, destination=new_file_path)
