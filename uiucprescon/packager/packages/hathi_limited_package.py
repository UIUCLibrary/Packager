"""limited-view content received from HathiTrust

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
import typing

from . import collection_builder
from .abs_package_builder import AbsPackageBuilder
from .collection import Package


class HathiLimitedView(AbsPackageBuilder):
    def locate_packages(self, path) -> typing.Iterator[Package]:
        builder = collection_builder.HathiLimitedViewBuilder()
        batch = builder.build_batch(path)
        for package in batch:
            yield package

    def transform(self, package: Package, dest: str) -> None:
        raise NotImplementedError("This package format can't be created")
