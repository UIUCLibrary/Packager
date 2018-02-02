import os

from behave import *
import re
import packager
import packager.packages

use_step_matcher("re")
CAPTURE_ONE_BATCH_NAME = "capture_one_batch"
HATHI_TIFF_BATCH_NAME = "hathi_tiff_batch"
DESTINATION_NAME = "out"


@given("We have a flat folder contains files that belong to two groups, grouped by the number left of an underscore")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    test_dir = context.temp_dir

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


@when("we create a CaptureOne object factory and use it to identify packages at the root folder")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    source = os.path.join(context.temp_dir, CAPTURE_ONE_BATCH_NAME)

    capture_one_packages_factory = packager.PackageFactory(packager.packages.CaptureOnePackage())
    # find all Capture One organized packages
    context.packages = list(capture_one_packages_factory.locate_packages(path=source))


@then("resulting packages should be 2")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    assert len(context.packages) == 2


@step("the first Capture One object should contain everything from the first group")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    package_objects = sorted(context.packages, key=lambda p: p.metadata['id'])
    object_000001 = package_objects[0]

    assert object_000001.metadata['id'] == "000001"

    assert len(object_000001) == 3

    # Every file here should start with 000001
    checker = re.compile("^000001_\d{8}\.tif$")

    for item in object_000001:
        for instance_type, instance in item.instantiations.items():
            for file_ in instance.files:
                basename = os.path.basename(file_)
                assert checker.match(basename)



@step("the second Capture One object should contain everything from the second group")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    pass
    package_objects = sorted(context.packages, key=lambda p: p.metadata['id'])
    object_000002 = package_objects[1]
    assert object_000002.metadata['id'] == "000002"

    assert len(object_000002) == 2

    # Every file here should start with 000002
    checker = re.compile("^000002_\d{8}\.tif$")

    for item in object_000002:
        for instance_type, instance in item.instantiations.items():
            for file_ in instance.files:
                basename = os.path.basename(file_)
                assert checker.match(basename)


@given("We have hathi tiff package containing a folder made up of 2 objects")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    test_dir = context.temp_dir
    hathi_batch = os.path.join(test_dir, HATHI_TIFF_BATCH_NAME)
    hathi_package_one_path = os.path.join(hathi_batch, "000001")
    hathi_package_two_path = os.path.join(hathi_batch, "000002")

    # Create the directory for the batch
    os.makedirs(hathi_batch)

    # Create the directories for the packages
    os.makedirs(hathi_package_one_path)
    os.makedirs(hathi_package_two_path)

    # Create a bunch of empty files that represent the files

    with open(os.path.join(hathi_package_one_path, "00000001.tif"), "w"):
        pass
    with open(os.path.join(hathi_package_one_path, "00000002.tif"), "w"):
        pass
    with open(os.path.join(hathi_package_one_path, "00000003.tif"), "w"):
        pass

    with open(os.path.join(hathi_package_two_path, "00000001.tif"), "w"):
        pass
    with open(os.path.join(hathi_package_two_path, "00000002.tif"), "w"):
        pass


@when("we create a HathiTiff object factory and use it to identify packages at the root folder")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    package_batch_path = os.path.join(context.temp_dir, HATHI_TIFF_BATCH_NAME)
    hathi_tiff_packages_factory = packager.PackageFactory(packager.packages.HathiTiff())

    # find all Capture One organized packages
    context.packages = list(hathi_tiff_packages_factory.locate_packages(path=package_batch_path))


@step("the first Hathi TIFF object should contain everything from the first group")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    package_objects = sorted(context.packages, key=lambda p: p.metadata['id'])
    object_000001 = package_objects[0]
    assert object_000001.metadata['id'] == "000001"

    assert len(object_000001) == 3

    # Every file here should start with 000001
    checker = re.compile("^\d{8}\.tif$")


    for item in object_000001:
        for instance_type, instance in item.instantiations.items():
            for file_ in instance.files:
                basename = os.path.basename(file_)
                assert checker.match(basename)


@step("the second Hathi TIFF object should contain everything from the second group")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    package_objects = sorted(context.packages, key=lambda p: p.metadata['id'])
    object_000002 = package_objects[1]
    assert object_000002.metadata['id'] == "000002"

    assert len(object_000002) == 2

    # Every file here should start with 000001
    checker = re.compile("^\d{8}\.tif$")


    for item in object_000002:
        for instance_type, instance in item.instantiations.items():
            for file_ in instance.files:
                basename = os.path.basename(file_)
                assert checker.match(basename)
