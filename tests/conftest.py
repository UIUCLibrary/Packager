import os
import shutil
import sys
import tempfile
from zipfile import ZipFile

import pytest
from typing import NamedTuple, Dict
import pathlib

from uiucprescon import packager


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


@pytest.fixture(scope="module", params=["uiuc.40", "uiuc.40834v1", "uiuc.5285248v1924"])
def hathi_limited_view_sample_packages(tmpdir_factory, request):
    test_dir = tmpdir_factory.mktemp("hathi_limited")
    sample_package_names = {
        "uiuc.40": [
            (
                "40.mets.xml",
                (
                    "40",
                    [
                        "40.mets.xml"
                    ] +
                    [f"{str(a).zfill(7)}.txt" for a in range(282)] +
                    [f"{str(a).zfill(7)}.jp2" for a in range(282)] +
                    [f"{str(a).zfill(7)}.xml" for a in range(282)]
                )
            )
        ],
        "uiuc.40834v1": [
            (
                "40834v1.mets.xml",
                (
                    "40834v1",
                    [
                        "40834v1.mets.xml"
                    ] +
                    [f"{str(a).zfill(7)}.txt" for a in range(256)] +
                    [f"{str(a).zfill(7)}.tif" for a in range(256)] +
                    [f"{str(a).zfill(7)}.xml" for a in range(256)]
                )
            )
        ],
        "uiuc.5285248v1924": [
            (
                "5285248v1924.mets.xml",
                (
                    "5285248v1924",
                    [
                        "5285248v1924.mets.xml"
                    ] +
                    [f"{str(a).zfill(7)}.txt" for a in range(282)] +
                    [f"{str(a).zfill(7)}.jp2" for a in range(282)] +
                    [f"{str(a).zfill(7)}.xml" for a in range(282)]
                )
            )
        ]
    }

    pkg_data = sample_package_names[request.param]
    pkg_dir = test_dir.join(request.param)
    os.makedirs(pkg_dir)
    with tempfile.TemporaryDirectory() as tmp_dir:
        for mets_file_filename, archive_data in pkg_data:
            with open(pkg_dir.join(mets_file_filename), "w"):
                # Create an empty file
                pass

            bib_id, zip_content = archive_data

            with ZipFile(pkg_dir.join(f"{bib_id}.zip"), 'w') as myzip:
                os.makedirs(os.path.join(tmp_dir, bib_id))
                for zipped_file in zip_content:
                    generated_file = os.path.join(tmp_dir, bib_id, zipped_file)
                    with open(generated_file, "w"):
                        # Create an empty file
                        pass

                    arcname = os.path.join(bib_id, zipped_file)
                    myzip.write(generated_file, arcname=arcname)

    hathi_limited_view_packager = packager.PackageFactory(
        packager.packages.HathiLimitedView())

    yield list(hathi_limited_view_packager.locate_packages(path=str(test_dir)))

    shutil.rmtree(test_dir)

