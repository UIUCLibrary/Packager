import typing
from . import collection_builder
from packager.packages.collection import Package
from .abs_package_builder import AbsPackageBuilder


class CaptureOnePackage(AbsPackageBuilder):

    def locate_packages(self, batch_path) -> typing.Iterator[Package]:
        for package in collection_builder.build_capture_one_batch(batch_path):
            yield package

    def copy(self, package, dest) -> None:
        pass
