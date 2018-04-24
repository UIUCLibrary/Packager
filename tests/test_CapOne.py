import os
from uiucprescon import packager
from uiucprescon.packager import packages
import pytest

CAPTURE_ONE_BATCH_NAME = "capture_one_batch"
DESTINATION_NAME = "out"


@pytest.fixture(scope="session")
def capture_one_fixture(tmpdir_factory):
    test_dir = tmpdir_factory.mktemp("test")

    os.makedirs(os.path.join(test_dir, CAPTURE_ONE_BATCH_NAME))
    os.makedirs(os.path.join(test_dir, DESTINATION_NAME))
    # Create a bunch of empty files that represent a capture one batch session

    with open(os.path.join(test_dir, CAPTURE_ONE_BATCH_NAME, "000001_00000001.tif"), "w"):
        pass
    with open(os.path.join(test_dir, CAPTURE_ONE_BATCH_NAME, "000001_00000002.tif"), "w"):
        pass
    with open(os.path.join(test_dir, CAPTURE_ONE_BATCH_NAME, "000001_00000003.tif"), "w"):
        pass
    with open(os.path.join(test_dir, CAPTURE_ONE_BATCH_NAME, "000002_00000001.tif"), "w"):
        pass
    with open(os.path.join(test_dir, CAPTURE_ONE_BATCH_NAME, "000002_00000002.tif"), "w"):
        pass

    return test_dir


def test_capture_one_tiff_to_hathi_tiff(capture_one_fixture):
    source = os.path.join(capture_one_fixture, CAPTURE_ONE_BATCH_NAME)
    dest = os.path.join(capture_one_fixture, DESTINATION_NAME)

    capture_one_packages_factory = packager.PackageFactory(packager.packages.CaptureOnePackage())
    # find all Capture One organized packages
    capture_one_packages = list(capture_one_packages_factory.locate_packages(path=source))
    # There should be 2 packages in this sample batch
    assert len(capture_one_packages) == 2

    hathi_tiff_package_factory = packager.PackageFactory(packager.packages.HathiTiff())
    for capture_one_package in capture_one_packages:
        hathi_tiff_package_factory.transform(capture_one_package, dest=dest)

    # This should result in the following files
    #
    # some_root/000001/00000001.tif
    # some_root/000001/00000002.tif
    # some_root/000001/00000003.tif
    assert os.path.exists(os.path.join(dest, "000001", "00000001.tif"))
    assert os.path.exists(os.path.join(dest, "000001", "00000002.tif"))
    assert os.path.exists(os.path.join(dest, "000001", "00000003.tif"))

    # some_root/000002/00000001.tif
    # some_root/000002/00000002.tif
    assert os.path.exists(os.path.join(dest, "000002", "00000001.tif"))
    assert os.path.exists(os.path.join(dest, "000002", "00000002.tif"))


def test_capture_one_tiff_package_size(capture_one_fixture):
    source = os.path.join(capture_one_fixture, CAPTURE_ONE_BATCH_NAME)
    capture_one_packages_factory = packager.PackageFactory(packager.packages.CaptureOnePackage())
    # find all Capture One organized packages
    capture_one_packages = list(capture_one_packages_factory.locate_packages(path=source))
    # There should be 2 packages in this sample batch
    assert len(capture_one_packages) == 2



def test_capture_one_tiff_to_digital_library(capture_one_fixture, monkeypatch):
    def make_access_jp2_replace(source_file_path, output_file_name):
        with open(output_file_name, "w") as f:
            pass
        pass

    monkeypatch.setattr(packager.packages.digital_library_compound, 'make_access_jp2', make_access_jp2_replace)
    source = os.path.join(capture_one_fixture, CAPTURE_ONE_BATCH_NAME)
    dest = os.path.join(capture_one_fixture, DESTINATION_NAME)


    capture_one_packages_factory = packager.PackageFactory(packager.packages.CaptureOnePackage())
    # find all Capture One organized packages
    capture_one_packages = list(capture_one_packages_factory.locate_packages(path=source))
    # There should be 2 packages in this sample batch
    assert len(capture_one_packages) == 2

    dl_factory = packager.PackageFactory(packager.packages.DigitalLibraryCompound())
    for capture_one_package in capture_one_packages:
        dl_factory.transform(capture_one_package, dest=dest)

    # This should result in the following files
    #
    #  some_root/000001/preservation/00000001.tif
    assert os.path.exists(os.path.join(dest, "000001", 'preservation', "000001_00000001.tif"))
    #  some_root/000001/access/
    assert os.path.exists(os.path.join(dest, "000001", 'access', "000001_00000001.jp2"))

    #  some_root/000001/preservation/00000002.tif
    assert os.path.exists(os.path.join(dest, "000001", 'preservation', "000001_00000002.tif"))
    #  some_root/000001/access/
    assert os.path.exists(os.path.join(dest, "000001", 'access', "000001_00000002.jp2"))

    #  some_root/000001/preservation/00000003.tif
    assert os.path.exists(os.path.join(dest, "000001", 'preservation', "000001_00000003.tif"))
    #  some_root/000001/access/
    assert os.path.exists(os.path.join(dest, "000001", 'access', "000001_00000003.jp2"))

    #  some_root/000002/preservation/00000001.tif
    assert os.path.exists(os.path.join(dest, "000002", "preservation", "000002_00000001.tif"))
    #  some_root/000002/access/
    assert os.path.exists(os.path.join(dest, "000002", "access", "000002_00000001.jp2"))

    #  some_root/000002/preservation/00000001.tif
    assert os.path.exists(os.path.join(dest, "000002", "preservation", "000002_00000001.tif"))
    #  some_root/000002/access/
    assert os.path.exists(os.path.join(dest, "000002", "access"))