import csv
import os

import pytest

from uiucprescon import packager
from uiucprescon.packager import InstantiationTypes
from uiucprescon.packager.packages.collection_builder import \
    HathiLimitedViewBuilder


def package_names():
    with open(os.path.join(os.path.dirname(__file__), "package_names.csv")) \
            as csvfile:
        for row in csv.reader(csvfile):
            yield row[0], True if row[1].strip() == "True" else False


@pytest.mark.parametrize("dirname,expected_valid", package_names())
def test_hathi_limited_batch_names(dirname, expected_valid):
    assert HathiLimitedViewBuilder.is_package_dir_name(dirname) \
           is expected_valid


sample_files = [
    ("dummy.txt", InstantiationTypes.SUPPLEMENTARY),
    ("dummy.TXT", InstantiationTypes.SUPPLEMENTARY),
    ("dummy.jp2", InstantiationTypes.ACCESS),
    ("dummy.JP2", InstantiationTypes.ACCESS),
    ("dummy.tif", InstantiationTypes.PRESERVATION),
    ("dummy.TIF", InstantiationTypes.PRESERVATION),
    ("dummy.exe", InstantiationTypes.UNKNOWN),
]


@pytest.mark.parametrize("sample_file,expected_valid", sample_files)
def test_get_file_type(sample_file, expected_valid):
    assert HathiLimitedViewBuilder.get_file_type(sample_file) == expected_valid
    assert True


def test_read_only_transform(capture_one_sample_package):

    capture_one_packager = packager.PackageFactory(
        packager.packages.CaptureOnePackage()
    )
    capture_one_packages = capture_one_packager.locate_packages(capture_one_sample_package)

    hathi_limited_view_packager = packager.PackageFactory(
        packager.packages.HathiLimitedView())
    with pytest.raises(NotImplementedError):
        hathi_limited_view_packager.transform(capture_one_packages, dest=".")
