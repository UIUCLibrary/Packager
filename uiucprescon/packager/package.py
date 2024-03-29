"""Package level."""

# This is the abstract factory
import typing
from .packages import collection
from .packages.abs_package_builder import AbsPackageBuilder


class PackageFactory:
    """Use for getting the correct type of file package."""

    def __init__(self, package_type: AbsPackageBuilder) -> None:
        """PackageFactory.

        Args:
            package_type: Package type used
        """
        self._package_type = package_type

    def locate_packages(
            self,
            path: str
    ) -> typing.Iterator[collection.Package]:
        """Locate packages for a given type.

        Args:
            path: File path to locate packages

        Yields:
            A new package if found

        """
        yield from self._package_type.locate_packages(path)

    def transform(self, package: collection.Package, dest: str) -> None:
        """Transform a given package into the current type.

        Args:
            package: Package to transform
            dest: File path to save the transformed package

        """
        self._package_type.transform(package, dest)
