from inspect import getmembers, isclass, isabstract
from packager import packages
from . import abs_package


class PackageFactory:
    packages = {}  # type: ignore

    def __init__(self):
        self.load_packages()

    def load_packages(self):

        classes = getmembers(packages, lambda m: isclass(m) and not isabstract(m))
        for name, _type in classes:
            if isclass(_type) and issubclass(_type, abs_package.AbsPackage):
                self.packages.update([[name, _type]])

    def create_instance(self, package_name, root):
        return self.packages[package_name](root)
