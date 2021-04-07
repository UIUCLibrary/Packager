import typing

from .abs_package_builder import AbsPackageBuilder
from .collection import Package
from . import collection_builder


class ArchivalNonEAS(AbsPackageBuilder):

    def locate_packages(self, path: str) -> typing.Iterator[Package]:
        package_builder = collection_builder.ArchivalNonEASBuilder()
        yield from package_builder.build_batch(path)

    def transform(self, package: Package, dest: str) -> None:
        raise NotImplementedError("ArchivalNonEAS can only be read")
