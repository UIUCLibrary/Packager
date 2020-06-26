import csv
import os

import pytest

from uiucprescon import packager
from uiucprescon.packager.packages.collection_builder import HathiLimitedViewBuilder


def package_names():
    with open(os.path.join(os.path.dirname(__file__), "package_names.csv")) as csvfile:
        for row in csv.reader(csvfile):
            yield row[0], True if row[1].strip() == "True" else False

@pytest.mark.parametrize("dirname,expected_valid", package_names())
def test_hathi_limited_batch_names(dirname,expected_valid):
    assert HathiLimitedViewBuilder.filter_package_dir_name(dirname) is expected_valid

source = "/Users/hborcher/PycharmProjects/Packager/testdata"
# def test_hathi_limited():
#     hathi_limited_packages_factory = packager.PackageFactory(
#         packager.packages.HathiLimitedView())
#
#     packages = \
#         list(hathi_limited_packages_factory.locate_packages(path=source))
#     assert len(packages) == 3
#
#
# @pytest.mark.parametrize("package", [0, 1, 2])
# def test_hathi_limited_convert(package):
#     hathi_limited_packages_factory = packager.PackageFactory(
#         packager.packages.HathiLimitedView())
#
#     packages = \
#         list(hathi_limited_packages_factory.locate_packages(path=source))
#
#     dl = packager.PackageFactory(
#         packager.packages.DigitalLibraryCompound())
#     dl.transform(packages[package], dest="/Users/hborcher/PycharmProjects/Packager/temp")
#
#     # hathi_limited_packages_factory.transform()
# #
# #
# #
#
#
