import os.path
from unittest.mock import Mock, call, ANY

import pytest

from uiucprescon.packager.packages import \
    digital_library_compound, collection
from uiucprescon import packager


class TestUseAccessTiffs:
    @pytest.fixture()
    def item(self):
        item = collection.Item()
        item.component_metadata[packager.Metadata.ID] = '99127822912205899'
        item.component_metadata[packager.Metadata.ITEM_NAME] = '001'
        item.component_metadata[packager.Metadata.PATH] = 'somepath'

        access_file = \
            collection.Instantiation(
                parent=item,
                category=packager.InstantiationTypes.ACCESS,
                files=["99127822912205899-001.tif"]
            )
        access_file.component_metadata[packager.Metadata.PATH] = \
            os.path.join("somepath", "access")

        preservation_file = \
            collection.Instantiation(
                parent=item,
                category=packager.InstantiationTypes.PRESERVATION,
                files=["99127822912205899-001.tif"]
            )
        preservation_file.component_metadata[packager.Metadata.PATH] = \
            os.path.join("somepath", "preservation")

        supplementary_data_files = collection.Instantiation(
            parent=item,
            category=packager.InstantiationTypes.SUPPLEMENTARY,
            files=[
                "99127822912205899-001a.txt",
                "99127822912205899-001b.txt",
            ]
        )
        supplementary_data_files.component_metadata[packager.Metadata.PATH] = \
            "somepath"

        return item

    def test_preservation_used_for_preservation(self, item):
        strategy = digital_library_compound.UseAccessTiffs()
        strategy.process = Mock()
        strategy.transform_preservation_file(item, dest="dummy")

        strategy.process.assert_called_with(
            source=os.path.join(
                "somepath",
                "preservation",
                "99127822912205899-001.tif"
            ),
            dest=os.path.join(
                "dummy",
                "99127822912205899",
                "preservation",
                "99127822912205899-001.tif"
            ),
            strategy=packager.transformations.CopyFile,
            logger=ANY
        )

    def test_access_used_for_access(self, item):
        strategy = digital_library_compound.UseAccessTiffs()
        strategy.process = Mock()
        strategy.transform_access_file(item, dest="dummy")

        strategy.process.assert_called_with(
            source=os.path.join(
                "somepath",
                "access",
                "99127822912205899-001.tif"
            ),
            dest=os.path.join(
                "dummy",
                "99127822912205899",
                "access",
                "99127822912205899-001.jp2"
            ),
            strategy=packager.transformations.ConvertJp2Standard,
            logger=ANY
        )

    def test_supplementary(self, item):
        strategy = digital_library_compound.UseAccessTiffs()
        strategy.process = Mock()
        strategy.transform_supplementary_data(item, dest="dummy")
        assert call(
            source=os.path.join("somepath", "99127822912205899-001a.txt"),
            dest=os.path.join(
                "dummy",
                "99127822912205899",
                "supplementary",
                "99127822912205899-001a.txt"
            ),
            strategy=packager.transformations.CopyFile,
            logger=ANY
        ) in strategy.process.call_args_list

