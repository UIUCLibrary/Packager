import os
import typing

from . import abs_package


class CaptureOnePackage(abs_package.AbsPackage):
    @staticmethod
    def get_packages(path) -> typing.Iterable[abs_package.PackageItem]:
        for package_path in filter(lambda x: x.is_file(), os.scandir(path)):
            yield abs_package.PackageItem(
                root=package_path.path,
                identifier=package_path.name,
                directories={
                    "access": package_path.path,
                }
            )