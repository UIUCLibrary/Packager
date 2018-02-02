.. _usage:

Usage
=====

Example
-------

.. code-block:: python

    cap_one_pkg_factory = packager.PackageFactory(packager.packages.CaptureOnePackage())

    # find all Capture One organized packages
    cap_one_packages = cap_one_pkg_factory .locate_packages(path=source)

    ht_tiff_pkg_factory = packager.PackageFactory(packager.packages.HathiTiff())
    for capture_one_package in cap_one_packages:
        # copy the packages into the new destination as a hathi tiff package
        ht_tiff_pkg_factory.transform(capture_one_package, dest)
