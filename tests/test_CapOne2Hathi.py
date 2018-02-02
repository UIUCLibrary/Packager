import os
import packager
import packager.packages
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