.. _usage:

Usage
=====


.. testsetup:: *

    import packager

    import tempfile
    import os

    temp_dir = tempfile.TemporaryDirectory()

    test_dir = temp_dir.name

    CAPTURE_ONE_BATCH_NAME = "capt"
    DESTINATION_NAME = "dest"

    CAPTURE_ONE_PATH = os.path.join(test_dir, CAPTURE_ONE_BATCH_NAME)
    DESTINATION_PATH = os.path.join(test_dir, DESTINATION_NAME)


    os.makedirs(CAPTURE_ONE_PATH)
    os.makedirs(DESTINATION_PATH)
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


    source = CAPTURE_ONE_PATH
    dest = DESTINATION_PATH

* Load an existing package batch with the PackageFactory class

.. doctest::

    >>> cap_one_pkg_factory = packager.PackageFactory(packager.packages.CaptureOnePackage())
    >>> cap_one_packages = cap_one_pkg_factory.locate_packages(path=source)
    >>> for capture_one_package in cap_one_packages:
    ...     print(capture_one_package.metadata['id'])
    000001
    000002





* To create new packages in another style, use the transform method from the desired package factory class.

.. testcode:: [capture_one_transform]

    cap_one_pkg_factory = packager.PackageFactory(packager.packages.CaptureOnePackage())

    # find all Capture One organized packages
    cap_one_packages = cap_one_pkg_factory.locate_packages(path=source)

    ht_tiff_pkg_factory = packager.PackageFactory(packager.packages.HathiTiff())
    for capture_one_package in cap_one_packages:
        # copy the packages into the new destination as a hathi tiff package
        ht_tiff_pkg_factory.transform(capture_one_package, dest)

.. testcode:: [capture_one_transform]
    :hide:

    assert os.path.exists(os.path.join(dest, "000001", "00000001.tif"))
    assert os.path.exists(os.path.join(dest, "000001", "00000002.tif"))
    assert os.path.exists(os.path.join(dest, "000001", "00000003.tif"))

    assert os.path.exists(os.path.join(dest, "000002", "00000001.tif"))
    assert os.path.exists(os.path.join(dest, "000002", "00000002.tif"))


