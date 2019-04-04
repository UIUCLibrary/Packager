import os
import shutil

from pytest_bdd import scenario, given, when, then
from ..conftest import sample_packages
from uiucprescon import packager
import pytest


@pytest.fixture
def new_path(tmpdir_factory):
    test_dir = tmpdir_factory.mktemp("out_bdd", numbered=False)
    yield test_dir
    shutil.rmtree(test_dir)


@scenario("package_transform.feature",
          "package containing 2 objects and want to transform them into a "
          "another type of package"
          )
def test_capture_one_session_two_object():
    pass


@given("A package containing 2 objects")
def package_objects(source_path, source_package_type):
    source_pkg = eval(f"packager.packages.{source_package_type}")
    source = os.path.join(source_path, sample_packages[source_package_type][0])

    packages_factory = packager.PackageFactory(source_pkg())
    packages = list(packages_factory.locate_packages(path=source))
    return packages


@given("We have another path to save the objects to")
def new_path_to_save_to(new_path, new_package_type):
    dest = os.path.join(new_path, new_package_type)
    os.mkdir(dest)
    return dest


@when("we transform all the packages found into the new package format")
def step_impl(package_objects, new_path_to_save_to, new_package_type):
    dest_pkg = eval(f"packager.packages.{new_package_type}")
    new_package_factory = dest_pkg()
    for package in package_objects:
        new_package_factory.transform(package, new_path_to_save_to)


@then("the newly transformed package should contain the same files but in the "
      "new format")
def step_impl(new_path_to_save_to, new_package_type):
    if new_package_type == "HathiTiff":
        assert os.path.exists(
            os.path.join(new_path_to_save_to, "000001", "00000001.tif"))
        assert os.path.exists(
            os.path.join(new_path_to_save_to, "000001", "00000002.tif"))
        assert os.path.exists(
            os.path.join(new_path_to_save_to, "000001", "00000003.tif"))
        assert os.path.exists(
            os.path.join(new_path_to_save_to, "000002", "00000001.tif"))
        assert os.path.exists(
            os.path.join(new_path_to_save_to, "000002", "00000002.tif"))
    elif new_package_type == "CaptureOnePackage":

        assert os.path.exists(
            os.path.join(new_path_to_save_to, "000001_00000001.tif"))
        assert os.path.exists(
            os.path.join(new_path_to_save_to, "000001_00000002.tif"))
        assert os.path.exists(
            os.path.join(new_path_to_save_to, "000001_00000003.tif"))

        assert os.path.exists(
            os.path.join(new_path_to_save_to, "000002_00000001.tif"))
        assert os.path.exists(
            os.path.join(new_path_to_save_to, "000002_00000002.tif"))
    else:
        pytest.fail("No test for {}".format(new_package_type))


@scenario("package_transform.feature",
          "Capture One session with a .DS_Store file transform to a HathiTrust "
          "Tiff package"
          )
def test_capture_one_session_two_object_and_ds_store():
    pass


@given("A Capture One session package containing 2 objects and a .DS_Store "
       "file in it")
def capture_one_session_w_ds_store(capture_one_sample_package):
    source_dir = os.path.join(capture_one_sample_package)

    with open(os.path.join(source_dir, ".DS_Store"), "w") as wf:
        pass
    capture_one_packages_factory = \
        packager.PackageFactory(packager.packages.CaptureOnePackage())

    # find all Capture One organized packages
    return list(capture_one_packages_factory.locate_packages(path=source_dir))


@when("we transform all the packages found into a HathiTiff Package")
def step_impl(capture_one_session_w_ds_store, new_path):
    hathi_tiff_packages_factory = \
        packager.PackageFactory(packager.packages.HathiTiff())
    dest = os.path.join(new_path, "HathiTiff")
    for package in capture_one_session_w_ds_store:
        hathi_tiff_packages_factory.transform(package, dest)


@then("The resulting package is a HathiTiff Package")
def step_impl(new_path):
    new_package = os.path.join(new_path, "HathiTiff")
    assert os.path.exists(os.path.join(new_package, "000001", "00000001.tif"))
    assert os.path.exists(os.path.join(new_package, "000001", "00000002.tif"))
    assert os.path.exists(os.path.join(new_package, "000001", "00000003.tif"))
    assert os.path.exists(os.path.join(new_package, "000002", "00000001.tif"))
    assert os.path.exists(os.path.join(new_package, "000002", "00000002.tif"))


@scenario("package_transform.feature",
          "Capture One session with a thumbs.db file transform to a HathiTrust "
          "Tiff package"
          )
def test_capture_one_session_two_object_and_thumbs():
    pass


@given("A Capture One session package containing 2 objects and a thumbs.db "
       "file in it")
def capture_one_session_w_thumbs(capture_one_sample_package):
    source_dir = os.path.join(capture_one_sample_package)

    with open(os.path.join(source_dir, "Thumbs.db"), "w") as wf:
        pass
    capture_one_packages_factory = \
        packager.PackageFactory(packager.packages.CaptureOnePackage())

    # find all Capture One organized packages
    return list(capture_one_packages_factory.locate_packages(path=source_dir))
