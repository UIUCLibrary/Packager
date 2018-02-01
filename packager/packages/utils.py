from dcc_qc.packages.package_factory import PackageFactory
from dcc_qc.packages import abs_package


def create_package(factory_name, root_path=None) -> abs_package.AbsPackage:
    packages = PackageFactory()
    return packages.create_instance(factory_name, root_path)
