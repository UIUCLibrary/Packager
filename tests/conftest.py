# from .source_path import source_path
import os
import shutil

import pytest
from typing import NamedTuple, Dict


class PackageTestType(NamedTuple):
    sub_path: str
    packaging_one_regex: str
    packaging_two_regex: str



sample_packages: Dict[str, PackageTestType] = {
    "CaptureOnePackage": PackageTestType("capture_one_batch", r"^000001_\d{8}\.tif$", r"^000002_\d{8}\.tif$"),
    "HathiTiff": PackageTestType("hathi_tiff_batch", r"^\d{8}\.tif$", r"^\d{8}\.tif$"),
    "HathiJp2": PackageTestType("hathi_jp2_batch", r"^\d{8}\.jp2$", r"^\d{8}\.jp2$"),
    "DigitalLibraryCompound": PackageTestType("Digital_Library_batch", r"^\d{6}_\d{8}\.(tif|jp2)$", r"^\d{6}_\d{8}\.(tif|jp2)$"),
    # "HATHI_JP2_BATCH_NAME": "hathi_jp2_batch",

}

@pytest.fixture
def capture_one_sample_package(tmpdir_factory):
    test_dir = tmpdir_factory.mktemp(
        sample_packages["CaptureOnePackage"].sub_path, numbered=False)
    #
    # c1_test_dir = \
    #     os.path.join(test_dir, capture_one_sample_package_name)

    # os.makedirs(test_dir)

    # Create a bunch of empty files that represent a capture one batch session
    with open(os.path.join(test_dir, "000001_00000001.tif"), "w"):
        pass
    with open(os.path.join(test_dir, "000001_00000002.tif"), "w"):
        pass
    with open(os.path.join(test_dir, "000001_00000003.tif"), "w"):
        pass
    with open(os.path.join(test_dir, "000002_00000001.tif"), "w"):
        pass
    with open(os.path.join(test_dir,  "000002_00000002.tif"), "w"):
        pass
    yield test_dir
    shutil.rmtree(test_dir)


@pytest.fixture
def hathi_tiff_sample_package(tmpdir_factory):
    test_dir = tmpdir_factory.mktemp(
        sample_packages["HathiTiff"].sub_path, numbered=False)

    hathi_package_one_path = \
        os.path.join(test_dir, "000001")

    os.makedirs(hathi_package_one_path)
    with open(os.path.join(hathi_package_one_path, "00000001.tif"), "w"):
        pass
    with open(os.path.join(hathi_package_one_path, "00000002.tif"), "w"):
        pass
    with open(os.path.join(hathi_package_one_path, "00000003.tif"), "w"):
        pass

    hathi_package_two_path = \
        os.path.join(test_dir, "000002")

    os.makedirs(hathi_package_two_path)
    with open(os.path.join(hathi_package_two_path, "00000001.tif"), "w"):
        pass
    with open(os.path.join(hathi_package_two_path, "00000002.tif"), "w"):
        pass
    yield test_dir
    shutil.rmtree(test_dir)


@pytest.fixture
def hathi_jp2_sample_package(tmpdir_factory):
    test_dir = tmpdir_factory.mktemp(
        sample_packages["HathiJp2"].sub_path, numbered=False)

    hathi_package_one_path = \
        os.path.join(test_dir, "000001")

    os.makedirs(hathi_package_one_path)
    with open(os.path.join(hathi_package_one_path, "00000001.jp2"), "w"):
        pass
    with open(os.path.join(hathi_package_one_path, "00000002.jp2"), "w"):
        pass
    with open(os.path.join(hathi_package_one_path, "00000003.jp2"), "w"):
        pass

    hathi_package_two_path = \
        os.path.join(test_dir, "000002")

    os.makedirs(hathi_package_two_path)
    with open(os.path.join(hathi_package_two_path, "00000001.jp2"), "w"):
        pass
    with open(os.path.join(hathi_package_two_path, "00000002.jp2"), "w"):
        pass
    yield test_dir
    shutil.rmtree(test_dir)


@pytest.fixture
def digital_library_compound_sample_package(tmpdir_factory):
    # ///// DigitalLibraryCompound
    test_dir = tmpdir_factory.mktemp(
        sample_packages["DigitalLibraryCompound"].sub_path, numbered=False)
    dl_compound_package_one = os.path.join(test_dir, "000001")
    os.makedirs(os.path.join(dl_compound_package_one, "preservation"))
    os.makedirs(os.path.join(dl_compound_package_one, "access"))


    # Create a bunch of empty files that represent a digital library
    # compound object batch
    with open(os.path.join(dl_compound_package_one, "preservation",
                           "000001_00000001.tif"), "w"):
        pass
    with open(os.path.join(dl_compound_package_one, "access",
                           "000001_00000001.jp2"), "w"):
        pass

    with open(os.path.join(dl_compound_package_one, "preservation",
                           "000001_00000002.tif"), "w"):
        pass
    with open(os.path.join(dl_compound_package_one, "access",
                           "000001_00000002.jp2"), "w"):
        pass

    with open(os.path.join(dl_compound_package_one, "preservation",
                           "000001_00000003.tif"), "w"):
        pass
    with open(os.path.join(dl_compound_package_one, "access",
                           "000001_00000003.jp2"), "w"):
        pass

    dl_compound_package_two = os.path.join(
        test_dir, "000002"
    )
    os.makedirs(os.path.join(dl_compound_package_two, "preservation"))
    os.makedirs(os.path.join(dl_compound_package_two, "access"))
    with open(os.path.join(
            dl_compound_package_two, "preservation", "000002_00000001.tif"), "w"):
        pass
    with open(os.path.join(
            dl_compound_package_two, "access", "000002_00000001.jp2"), "w"):
        pass

    with open(os.path.join(
            dl_compound_package_two, "preservation", "000002_00000002.tif"), "w"):
        pass

    with open(os.path.join(
            dl_compound_package_two, "access", "000002_00000002.jp2"), "w"):
        pass
    yield test_dir
    shutil.rmtree(test_dir)


@pytest.fixture
def source_path(tmpdir_factory, capture_one_sample_package, hathi_tiff_sample_package, digital_library_compound_sample_package):
    test_dir = tmpdir_factory.mktemp("source_path", numbered=False)

    shutil.copytree(
        capture_one_sample_package,
        os.path.join(test_dir, sample_packages["CaptureOnePackage"].sub_path))

    shutil.copytree(
        hathi_tiff_sample_package,
        os.path.join(test_dir, sample_packages["HathiTiff"].sub_path))

    shutil.copytree(
        digital_library_compound_sample_package,
        os.path.join(test_dir,
                     sample_packages["DigitalLibraryCompound"].sub_path))

    yield test_dir
    shutil.rmtree(test_dir)

