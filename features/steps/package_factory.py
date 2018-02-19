import os

from behave import *
import re
import uiucprescon.packager
import uiucprescon.packager.packages
from uiucprescon.packager.packages.collection import Metadata, PackageTypes, InstantiationTypes

DL_COMPOUND_NAME = "digital_library_compound"

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

    capture_one_packages_factory = uiucprescon.packager.PackageFactory(
        uiucprescon.packager.packages.CaptureOnePackage())
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
    package_objects = sorted(context.packages, key=lambda p: p.metadata[Metadata.ID])
    object_000001 = package_objects[0]

    assert object_000001.metadata[Metadata.ID] == "000001"

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
    package_objects = sorted(context.packages, key=lambda p: p.metadata[Metadata.ID])
    object_000002 = package_objects[1]
    assert object_000002.metadata[Metadata.ID] == "000002"

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
    hathi_tiff_packages_factory = uiucprescon.packager.PackageFactory(uiucprescon.packager.packages.HathiTiff())

    # find all Capture One organized packages
    context.packages = list(hathi_tiff_packages_factory.locate_packages(path=package_batch_path))


@step("the first Hathi TIFF object should contain everything from the first group")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    package_objects = sorted(context.packages, key=lambda p: p.metadata[Metadata.ID])
    object_000001 = package_objects[0]
    assert object_000001.metadata[Metadata.ID] == "000001"

    assert len(object_000001) == 3

    # Every file here should have 8 digits in it
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
    package_objects = sorted(context.packages, key=lambda p: p.metadata[Metadata.ID])
    object_000002 = package_objects[1]
    assert object_000002.metadata[Metadata.ID] == "000002"

    assert len(object_000002) == 2

    # Every file here should have 8 digits in it
    checker = re.compile("^\d{8}\.tif$")

    for item in object_000002:
        for instance_type, instance in item.instantiations.items():
            for file_ in instance.files:
                basename = os.path.basename(file_)
                assert checker.match(basename)


@step("we transform all the packages found into Hathi tiff packages")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """

    dest = os.path.join(context.temp_dir, DESTINATION_NAME)
    os.makedirs(dest)

    hathi_tiff_package_factory = uiucprescon.packager.PackageFactory(uiucprescon.packager.packages.HathiTiff())

    for capture_one_package in context.packages:
        hathi_tiff_package_factory.transform(capture_one_package, dest=dest)


@then("the newly transformed package should contain the same files but in the format for Hathi Trust")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    dest = os.path.join(context.temp_dir, DESTINATION_NAME)

    assert os.path.exists(os.path.join(dest, "000001", "00000001.tif"))
    assert os.path.exists(os.path.join(dest, "000001", "00000002.tif"))
    assert os.path.exists(os.path.join(dest, "000001", "00000003.tif"))

    # some_root/000002/00000001.tif
    # some_root/000002/00000002.tif
    assert os.path.exists(os.path.join(dest, "000002", "00000001.tif"))
    assert os.path.exists(os.path.join(dest, "000002", "00000002.tif"))


@step("we transform all the packages found into Capture One packages")
def step_impl(context):
    """
    Args:
        context (behave.runner.Context):
    """
    dest = os.path.join(context.temp_dir, DESTINATION_NAME)
    os.makedirs(dest)

    capture_one_factory = uiucprescon.packager.PackageFactory(uiucprescon.packager.packages.CaptureOnePackage())

    for hathi_tiff_package in context.packages:
        capture_one_factory.transform(hathi_tiff_package, dest=dest)


@then("the newly transformed package should contain the same files but in the format for Capture One")
def step_impl(context):
    """
    Args:
        context (behave.runner.Context):
    """
    dest = os.path.join(context.temp_dir, DESTINATION_NAME)

    assert os.path.exists(os.path.join(dest, "000001_00000001.tif"))
    assert os.path.exists(os.path.join(dest, "000001_00000002.tif"))
    assert os.path.exists(os.path.join(dest, "000001_00000003.tif"))

    # some_root/000002/00000001.tif
    # some_root/000002/00000002.tif
    assert os.path.exists(os.path.join(dest, "000002_00000001.tif"))
    assert os.path.exists(os.path.join(dest, "000002_00000002.tif"))


@step("we transform all the packages found into Digital Library Compound Objects packages")
def step_impl(context):
    """
    Args:
        context (behave.runner.Context):
    """
    dest = os.path.join(context.temp_dir, DESTINATION_NAME)
    os.makedirs(dest)

    digital_factory = uiucprescon.packager.PackageFactory(uiucprescon.packager.packages.DigitalLibraryCompound())

    for hathi_tiff_package in context.packages:
        digital_factory.transform(hathi_tiff_package, dest=dest)


@then(
    "the newly transformed package should contain the same files but in the format for Digital Library Compound Objects")
def step_impl(context):
    """
    Args:
        context (behave.runner.Context):
    """
    dest = os.path.join(context.temp_dir, DESTINATION_NAME)

    assert os.path.exists(os.path.join(dest, "000001", 'preservation', "000001_00000001.tif"))
    assert os.path.exists(os.path.join(dest, "000001", 'access'))

    assert os.path.exists(os.path.join(dest, "000001", 'preservation', "000001_00000002.tif"))
    assert os.path.exists(os.path.join(dest, "000001", 'access'))

    assert os.path.exists(os.path.join(dest, "000001", 'preservation', "000001_00000003.tif"))
    assert os.path.exists(os.path.join(dest, "000001", 'access'))

    assert os.path.exists(os.path.join(dest, "000002", "preservation", "000002_00000001.tif"))
    assert os.path.exists(os.path.join(dest, "000002", "access"))

    assert os.path.exists(os.path.join(dest, "000002", "preservation", "000002_00000001.tif"))
    assert os.path.exists(os.path.join(dest, "000002", "access"))


@given("We have a folder contains two Digital Library Compound objects")
def step_impl(context):
    """
    Args:
        context (behave.runner.Context):
    """
    test_dir = context.temp_dir

    os.makedirs(os.path.join(test_dir, DL_COMPOUND_NAME))

    # Create a folder structure that represent a digital library compound object batch
    os.makedirs(os.path.join(test_dir, DL_COMPOUND_NAME, "000001", "preservation"))
    os.makedirs(os.path.join(test_dir, DL_COMPOUND_NAME, "000001", "access"))
    os.makedirs(os.path.join(test_dir, DL_COMPOUND_NAME, "000002", "preservation"))
    os.makedirs(os.path.join(test_dir, DL_COMPOUND_NAME, "000002", "access"))

    # Create a bunch of empty files that represent a digital library compound object batch
    with open(os.path.join(test_dir, DL_COMPOUND_NAME, "000001", "preservation", "000001_00000001.tif"), "w"):
        pass
    with open(os.path.join(test_dir, DL_COMPOUND_NAME, "000001", "access", "000001_00000001.jp2"), "w"):
        pass

    with open(os.path.join(test_dir, DL_COMPOUND_NAME, "000001", "preservation", "000001_00000002.tif"), "w"):
        pass
    with open(os.path.join(test_dir, DL_COMPOUND_NAME, "000001", "access", "000001_00000002.jp2"), "w"):
        pass

    with open(os.path.join(test_dir, DL_COMPOUND_NAME, "000001", "preservation", "000001_00000003.tif"), "w"):
        pass
    with open(os.path.join(test_dir, DL_COMPOUND_NAME, "000001", "access", "000001_00000003.jp2"), "w"):
        pass

    with open(os.path.join(test_dir, DL_COMPOUND_NAME, "000002", "preservation", "000002_00000001.tif"), "w"):
        pass
    with open(os.path.join(test_dir, DL_COMPOUND_NAME, "000002", "access", "000002_00000001.jp2"), "w"):
        pass

    with open(os.path.join(test_dir, DL_COMPOUND_NAME, "000002", "preservation", "000002_00000002.tif"), "w"):
        pass
    with open(os.path.join(test_dir, DL_COMPOUND_NAME, "000002", "access", "000002_00000002.jp2"), "w"):
        pass


@when("we create a Digital Library Compound object factory and use it to identify packages at the root folder")
def step_impl(context):
    """
    Args:
        context (behave.runner.Context):
    """
    source = os.path.join(context.temp_dir, DL_COMPOUND_NAME)

    digital_library_compound_factory = uiucprescon.packager.PackageFactory(
        uiucprescon.packager.packages.DigitalLibraryCompound())

    # find all Digital library Compount objects
    context.packages = list(digital_library_compound_factory.locate_packages(path=source))


@then("the resulting package should be a Digital Library Compound Object type")
def step_impl(context):
    """
    Args:
        context (behave.runner.Context):
    """
    for package in context.packages:
        assert package.metadata[Metadata.PACKAGE_TYPE] == PackageTypes.DIGITAL_LIBRARY_COMPOUND


@step("the first Digital Library Compound object should contain everything from the first group")
def step_impl(context):
    """
    Args:
        context (behave.runner.Context):
    """
    package_objects = sorted(context.packages, key=lambda p: p.metadata[Metadata.ID])
    object_000001 = package_objects[0]
    assert object_000001.metadata[Metadata.ID] == "000001"

    assert len(object_000001) == 3

    # Every file here should have 6 digits, underscore, 8 digits in it
    checker = re.compile("^\d{6}_\d{8}$")

    for item in object_000001:

        access = item.instantiations[InstantiationTypes.ACCESS]
        for file_ in access.files:
            file_name, ext = os.path.splitext(os.path.basename(file_))
            assert ext == ".jp2"
            assert checker.match(file_name)

        preservation = item.instantiations[InstantiationTypes.PRESERVATION]
        for file_ in preservation.files:
            file_name, ext = os.path.splitext(os.path.basename(file_))
            assert ext == ".tif"
            assert checker.match(file_name)


@step("the second Digital Library Compound object should contain everything from the second group")
def step_impl(context):
    """
    Args:
        context (behave.runner.Context):
    """
    package_objects = sorted(context.packages, key=lambda p: p.metadata[Metadata.ID])
    object_000002 = package_objects[1]
    assert object_000002.metadata[Metadata.ID] == "000002"

    assert len(object_000002) == 2

    # Every file here should have 6 digits, underscore, 8 digits in it
    checker = re.compile("^\d{6}_\d{8}\.((tif)|(jp2))$")

    for item in object_000002:
        for instance_type, instance in item.instantiations.items():
            for file_ in instance.files:
                basename = os.path.basename(file_)
                assert checker.match(basename)


@step("the folder flat folder has a Thumbs\.db file in it")
def step_impl(context):
    """
    Args:
        context (behave.runner.Context):
    """
    source_dir = os.path.join(context.temp_dir, CAPTURE_ONE_BATCH_NAME)
    with open(os.path.join(source_dir, "Thumbs.db"), "w") as wf:
        pass


@step("the folder flat folder has a \.DS_Store file in it")
def step_impl(context):
    """
    Args:
        context (behave.runner.Context):
    """
    source_dir = os.path.join(context.temp_dir, CAPTURE_ONE_BATCH_NAME)

    with open(os.path.join(source_dir, ".DS_Store"), "w") as wf:
        pass
