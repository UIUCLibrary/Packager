# This is the abstract factory
import typing
from .packages import collection
from .packages.abs_package_builder import AbsPackageBuilder


class PackageFactory:
    def __init__(self, package_type: AbsPackageBuilder) -> None:
        self._package_type = package_type

    def locate_packages(self, path) -> typing.Iterator[collection.Package]:
        for package in self._package_type.locate_packages(path):
            yield package

    def transform(self, package, dest: str):
        self._package_type.transform(package, dest)
