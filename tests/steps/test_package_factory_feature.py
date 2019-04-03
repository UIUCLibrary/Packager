import os
import re
import shutil
from uiucprescon import packager

from pytest_bdd import scenario, given, when, then
import pytest

from uiucprescon.packager import Metadata
from ..conftest import sample_packages


@scenario(
    "package_factory.feature",
    "Loading session containing 2 objects"
)
def test_load_session_objects():
    pass


@given("We have a object created by contains files that belong to two groups")
def package_objects(source_path, package_type):
    pkg_factory_type = eval(f"packager.packages.{package_type}")

    source = os.path.join(source_path, sample_packages[package_type][0])

    capture_one_packages_factory = packager.PackageFactory(pkg_factory_type())

    # find all Capture One organized packages
    packages = list(capture_one_packages_factory.locate_packages(path=source))
    return packages


@then("resulting packages should be 2")
def two_packages(package_objects):
    assert len(package_objects) == 2


@then("the first object should contain everything from the first group")
def step_impl(package_objects, package_type):
    first_group_regex = sample_packages[package_type][1]
    package_objects = sorted(package_objects,
                             key=lambda p: p.metadata[Metadata.ID])
    object_000001 = package_objects[0]

    assert object_000001.metadata[Metadata.ID] == "000001"

    assert len(object_000001) == 3

    # Every file here should start with 000001
    checker = re.compile(first_group_regex)

    for item in object_000001:
        for instance_type, instance in item.instantiations.items():
            for file_ in instance.files:
                basename = os.path.basename(file_)
                assert checker.match(basename)


@then("the second object should contain everything from the second group")
def step_impl(package_objects, package_type):
    second_group_regex = sample_packages[package_type][2]
    package_objects = sorted(package_objects,
                             key=lambda p: p.metadata[Metadata.ID])
    object_000002 = package_objects[1]
    assert object_000002.metadata[Metadata.ID] == "000002"

    assert len(object_000002) == 2

    # Every file here should start with 000002
    checker = re.compile(second_group_regex)

    for item in object_000002:
        for instance_type, instance in item.instantiations.items():
            for file_ in instance.files:
                basename = os.path.basename(file_)
                assert checker.match(basename)


@scenario("package_factory.feature",
          "Hathi TIFF package containing 2 objects with sidecar text files"
)
def test_hathi_tiff_two_object_and_sidecar_text():
    pass


@given("a hathi tiff package containing 2 objects with text sidecar files")
def hathi_tiff_package_w_sidecar_text(hathi_tiff_sample_package):
    package_one_path = os.path.join(hathi_tiff_sample_package, "000001")
    for i in range(3):
        with open(os.path.join(package_one_path, f"0000000{i+1}.txt"), "w"):
            pass

    package_two_path = os.path.join(hathi_tiff_sample_package, "000002")
    for i in range(2):
        with open(os.path.join(package_two_path, f"0000000{i+1}.txt"), "w"):
            pass
    package_factory = packager.PackageFactory(packager.packages.HathiTiff())

    packages = list(package_factory .locate_packages(hathi_tiff_sample_package))
    return packages


@then("resulting packages hathi tiff package should be 2")
def step_impl(hathi_tiff_package_w_sidecar_text):
    assert len(hathi_tiff_package_w_sidecar_text) == 2


@then("each instance of tiff package in should contain a text sidecar file")
def step_impl(hathi_tiff_package_w_sidecar_text):
    for package in hathi_tiff_package_w_sidecar_text:
        for item in package.items:
            for instance in item.instantiations.values():
                num_sidecar_file = len(instance.sidecar_files)
                if num_sidecar_file != 1:
                    pytest.fail(f"{instance} contains {num_sidecar_file} sidecare files")

@scenario("package_factory.feature",
          "Hathi jp2 package containing 2 objects with sidecar text files"
)
def test_hathi_jp2_two_object_and_sidecar_text():
    pass


@given("a hathi jp2 package containing 2 objects with text sidecar files")
def hathi_jp2_package_w_sidecar_text(hathi_jp2_sample_package):
    package_one_path = os.path.join(hathi_jp2_sample_package, "000001")
    for i in range(3):
        with open(os.path.join(package_one_path, f"0000000{i+1}.txt"), "w"):
            pass

    package_two_path = os.path.join(hathi_jp2_sample_package, "000002")
    for i in range(2):
        with open(os.path.join(package_two_path, f"0000000{i+1}.txt"), "w"):
            pass
    package_factory = packager.PackageFactory(packager.packages.HathiJp2())

    packages = list(package_factory.locate_packages(hathi_jp2_sample_package))
    return packages

@then("resulting packages hathi jp2 package should be 2")
def step_impl(hathi_jp2_package_w_sidecar_text):
    assert len(hathi_jp2_package_w_sidecar_text) == 2


@then("each instance in jp2 package should contain a text sidecar file")
def step_impl(hathi_jp2_package_w_sidecar_text):
    for package in hathi_jp2_package_w_sidecar_text:
        for item in package.items:
            for instance in item.instantiations.values():
                num_sidecar_file = len(instance.sidecar_files)
                if num_sidecar_file != 1:
                    pytest.fail(f"{instance} contains {num_sidecar_file} sidecare files")
