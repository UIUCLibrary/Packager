import typing

from packager.packages import collection_builder
from packager.packages.collection import Package
from .abs_package_builder import AbsPackageBuilder


class HathiTiff(AbsPackageBuilder):
    def locate_packages(self, batch_path) -> typing.Iterator[Package]:
        for package in collection_builder.build_hathi_tiff_batch(batch_path):
            yield package

    def copy(self, package, dest) -> None:
        pass
