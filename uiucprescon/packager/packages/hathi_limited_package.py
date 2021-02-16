"""limited-view content received from HathiTrust.

The three versions are as follows:

 UIUC.[BibID], e.g. 5285248v1924
    [BibID].mets
    [BibID].zip
        [page].txt
        [page].jp2
        [BibID].mets

UIUC.[BibID], e.g. 40834v1
    [BibID].mets
    [BibID].zip
        [page].tif
        [page].txt
        [BibID].mets


UIUC.[BibID], e.g. 40
    [BibID].mets
    [BibID].zip
        [page].txt
        [page].jp2
        [page].xml


"""
from typing import Iterator
from . import collection_builder
from .abs_package_builder import AbsPackageBuilder
from .collection import Package


class HathiLimitedView(AbsPackageBuilder):
    """limited-view content received from HathiTrust."""

    def locate_packages(self, path: str) -> Iterator[Package]:
        """Locate Hathi tiff packages on a given file path.

        Args:
            path: File path to search for Hathi limited view packages

        Yields:
            Hathi limited view packages

        """
        builder = collection_builder.HathiLimitedViewBuilder()
        batch = builder.build_batch(path)
        for package in batch:
            yield package

    def transform(self, package: Package, dest: str) -> None:
        """Invalid.

        This raises an exception. This is a read only format for now

        Args:
            package:
            dest:

        """
        raise NotImplementedError("This package format can't be created")
