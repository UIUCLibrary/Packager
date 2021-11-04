import os.path
from unittest.mock import Mock, MagicMock, call, ANY

import pytest

from uiucprescon.packager import packages
from uiucprescon.packager import package, common
from uiucprescon.packager.packages import collection
from uiucprescon import packager


class TestHathiJp2:
    @pytest.fixture
    def digital_library_object(self):

        new_object = collection.PackageObject()
        new_object.component_metadata[collection.Metadata.ID] = "123"

        new_object.component_metadata[collection.Metadata.PACKAGE_TYPE] = \
            common.PackageTypes.DIGITAL_LIBRARY_COMPOUND

        new_item = collection.Item(parent=new_object)

        new_item.component_metadata[collection.Metadata.ID] = "123"
        new_item.component_metadata[collection.Metadata.PATH] = "source"
        new_item.component_metadata[collection.Metadata.ITEM_NAME] = '00000001'

        collection.Instantiation(
            category=collection.InstantiationTypes.ACCESS,
            parent=new_item,
            files=[
                os.path.join("123", "access", "123-00000001.jp2")
            ]
        )

        collection.Instantiation(
            category=collection.InstantiationTypes.PRESERVATION,
            parent=new_item,
            files=[
                os.path.join(
                    "123", "preservation", "123-00000001.tif"
                )
            ]
        )
        return new_object

    def test_copy_jp2_access_to_hathi_jp2(
            self,
            digital_library_object,
            monkeypatch
    ):
        transform = Mock()
        monkeypatch.setattr(
            packager.transformations.Transformers,
            "transform",
            transform
        )
        package.PackageFactory(
            packages.hathi_jp2_package.HathiJp2()
        ).transform(digital_library_object, "out")

        expected_calls = [
            call(
                source=os.path.join(
                    "source",
                    "123",
                    "access",
                    "123-00000001.jp2"
                ),
                destination=os.path.join("out", "123", "00000001.jp2")
            ),
        ]
        assert expected_calls == transform.mock_calls


@pytest.fixture
def compound_item():
    new_item = collection.Item()

    new_item.component_metadata[collection.Metadata.ID] = "123"
    new_item.component_metadata[collection.Metadata.PATH] = "source"
    new_item.component_metadata[collection.Metadata.ITEM_NAME] = '00000001'
    collection.Instantiation(
        category=collection.InstantiationTypes.ACCESS,
        parent=new_item,
        files=[
            os.path.join("123", "access", "123-00000001.jp2")
        ]
    )

    collection.Instantiation(
        category=collection.InstantiationTypes.PRESERVATION,
        parent=new_item,
        files=[
            os.path.join(
                "123", "preservation", "123-00000001.tif"
            )
        ]
    )
    return new_item


class TestCopyStrategy:
    def test_transform_access(self, monkeypatch, compound_item):
        strategy = packages.hathi_jp2_package.CopyStrategy()
        strategy.transformer.transform = Mock()
        strategy.transform_access_file(compound_item, dest="out")
        assert strategy.transformer.transform.called is True
        expected_call = call(
            source=os.path.join("source", "123", "access", "123-00000001.jp2"),
            destination=os.path.join("out", "123", "00000001.jp2"),
        )

        assert expected_call in strategy.transformer.transform.mock_calls
        assert call(
            source=os.path.join(
                "source", "123", "preservation", "123-00000001.jp2"),
            destination=os.path.join("out", "123", "00000001.jp2"),
        ) not in strategy.transformer.transform.mock_calls


@pytest.fixture
def capture_one_item():
    capture_one_tiff = collection.Item()

    capture_one_tiff.component_metadata[collection.Metadata.ID] = "123"
    capture_one_tiff.component_metadata[collection.Metadata.PATH] = "source"
    capture_one_tiff.component_metadata[
        collection.Metadata.ITEM_NAME] = '00000001'

    collection.Instantiation(
        category=collection.InstantiationTypes.PRESERVATION,
        parent=capture_one_tiff,
        files=[
            os.path.join(
                "123", "123_00000001.tif"
            )
        ]
    )
    return capture_one_tiff


class TestConvertStrategy:

    def test_transform_access(self, capture_one_item):

        strategy = packages.hathi_jp2_package.ConvertStrategy(
            instance_source=collection.InstantiationTypes.PRESERVATION
        )
        strategy.convert = Mock()
        strategy.transform_access_file(capture_one_item, dest="out")
        assert strategy.convert.called is True
        assert call(
            os.path.join("source", "123", "123_00000001.tif"),
            os.path.join("out", "123",  "00000001.jp2"),
        ) in strategy.convert.mock_calls
