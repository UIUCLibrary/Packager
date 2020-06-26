import csv
import os

import pytest

from uiucprescon.packager.packages.collection_builder import \
    HathiLimitedViewBuilder


def package_names():
    with open(os.path.join(os.path.dirname(__file__), "package_names.csv")) \
            as csvfile:
        for row in csv.reader(csvfile):
            yield row[0], True if row[1].strip() == "True" else False


@pytest.mark.parametrize("dirname,expected_valid", package_names())
def test_hathi_limited_batch_names(dirname,expected_valid):
    assert HathiLimitedViewBuilder.filter_package_dir_name(dirname) \
           is expected_valid

