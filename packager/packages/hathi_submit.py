from .abs_package import AbsPackage, PackageItem
# from dcc_qc import packages
# import typing
import os
# import itertools
# from collections import namedtuple


class HathiSubmitPackage(AbsPackage):
    @staticmethod
    def get_packages(path):
        for package_path in filter(lambda x: x.is_dir(), os.scandir(path)):
            yield PackageItem(
                root=package_path.path,
                identifier=package_path.name,
                directories={
                    "access": package_path.path,
                }
            )
