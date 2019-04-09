import os
import shutil

import pytest
from typing import NamedTuple, Dict
import pathlib

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

    # Create a bunch of empty files that represent a capture one batch session
    for file_name in ["000001_00000001.tif",
                      "000001_00000002.tif",
                      "000001_00000003.tif",
                      "000002_00000001.tif",
                      "000002_00000002.tif"]:
        pathlib.Path(os.path.join(test_dir, file_name)).touch()

    yield test_dir
    shutil.rmtree(test_dir)


@pytest.fixture
def hathi_tiff_sample_package(tmpdir_factory):
    test_dir = tmpdir_factory.mktemp(
        sample_packages["HathiTiff"].sub_path, numbered=False)

    hathi_package_one_path = os.path.join(test_dir, "000001")
    os.makedirs(hathi_package_one_path)

    for file_name in ["00000001.tif",
                      "00000002.tif",
                      "00000003.tif"]:
        pathlib.Path(os.path.join(hathi_package_one_path, file_name)).touch()

    hathi_package_two_path = os.path.join(test_dir, "000002")
    os.makedirs(hathi_package_two_path)

    for file_name in ["00000001.tif",
                      "00000002.tif"]:
        pathlib.Path(os.path.join(hathi_package_two_path, file_name)).touch()

    yield test_dir
    shutil.rmtree(test_dir)


@pytest.fixture
def hathi_jp2_sample_package(tmpdir_factory):
    test_dir = tmpdir_factory.mktemp(
        sample_packages["HathiJp2"].sub_path, numbered=False)

    hathi_package_one_path = os.path.join(test_dir, "000001")

    os.makedirs(hathi_package_one_path)

    for file_name in ["00000001.jp2",
                      "00000002.jp2",
                      "00000003.jp2"]:
        pathlib.Path(os.path.join(hathi_package_one_path, file_name)).touch()

    hathi_package_two_path = os.path.join(test_dir, "000002")

    os.makedirs(hathi_package_two_path)
    for file_name in ["00000001.jp2",
                      "00000002.jp2"]:
        pathlib.Path(os.path.join(hathi_package_two_path, file_name)).touch()

    yield test_dir
    shutil.rmtree(test_dir)


@pytest.fixture
def digital_library_compound_sample_package(tmpdir_factory):
    # ///// DigitalLibraryCompound
    test_dir = tmpdir_factory.mktemp(
        sample_packages["DigitalLibraryCompound"].sub_path, numbered=False)
    dl_compound_package_one = os.path.join(test_dir, "000001")

    # Create a bunch of empty files that represent a digital library
    # compound object batch
    os.makedirs(os.path.join(dl_compound_package_one, "preservation"))
    for file_name in ["000001_00000001.tif",
                      "000001_00000002.tif",
                      "000001_00000003.tif"]:
        new_file_full = os.path.join(
            dl_compound_package_one, "preservation", file_name)

        pathlib.Path(new_file_full).touch()

    os.makedirs(os.path.join(dl_compound_package_one, "access"))
    for file_name in ["000001_00000001.jp2",
                      "000001_00000002.jp2",
                      "000001_00000003.jp2"]:
        new_file_full = os.path.join(
            dl_compound_package_one, "access", file_name)

        pathlib.Path(new_file_full).touch()

    dl_compound_package_two = os.path.join(test_dir, "000002")

    os.makedirs(os.path.join(dl_compound_package_two, "preservation"))
    for file_name in ["000002_00000001.tif",
                      "000002_00000002.tif"]:
        new_file_full = os.path.join(
            dl_compound_package_two, "preservation", file_name)
        pathlib.Path(new_file_full).touch()

    os.makedirs(os.path.join(dl_compound_package_two, "access"))

    for file_name in ["000002_00000001.jp2",
                      "000002_00000002.jp2"]:
        new_file_full = os.path.join(
            dl_compound_package_two, "access", file_name)
        pathlib.Path(new_file_full).touch()

    yield test_dir
    shutil.rmtree(test_dir)


@pytest.fixture
def source_path(tmpdir_factory, capture_one_sample_package, hathi_tiff_sample_package, digital_library_compound_sample_package):
    test_dir = tmpdir_factory.mktemp("source_packages", numbered=False)

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

