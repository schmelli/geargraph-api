import importlib.util
import sys
import types
import unittest
from pathlib import Path


class _GearItem:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


def _load_resolvers_module():
    app_module = types.ModuleType("app")
    db_module = types.ModuleType("app.db")
    memgraph_module = types.ModuleType("app.db.memgraph")
    schema_module = types.ModuleType("app.schema")
    schema_types_module = types.ModuleType("app.schema.types")

    memgraph_module.get_db = lambda: None
    schema_types_module.GearItem = _GearItem

    sys.modules["app"] = app_module
    sys.modules["app.db"] = db_module
    sys.modules["app.db.memgraph"] = memgraph_module
    sys.modules["app.schema"] = schema_module
    sys.modules["app.schema.types"] = schema_types_module

    resolvers_path = Path(__file__).resolve().parents[1] / "app" / "schema" / "resolvers.py"
    spec = importlib.util.spec_from_file_location("test_resolvers_module", resolvers_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


RESOLVERS = _load_resolvers_module()


class MapGearItemTests(unittest.TestCase):
    def test_prefers_normalized_image_url_field(self):
        item = RESOLVERS._map_gear_item(
            {
                "gearId": "gear-1",
                "name": "Shelter",
                "brand": "Durston",
                "image_url": "https://example.com/normalized.jpg",
                "imageUrl": "https://example.com/legacy.jpg",
            }
        )

        self.assertEqual(item.image_url, "https://example.com/normalized.jpg")

    def test_falls_back_to_legacy_image_url_field(self):
        item = RESOLVERS._map_gear_item(
            {
                "gearId": "gear-2",
                "name": "Stove",
                "brand": "Evernew",
                "imageUrl": "https://example.com/legacy.jpg",
            }
        )

        self.assertEqual(item.image_url, "https://example.com/legacy.jpg")


if __name__ == "__main__":
    unittest.main()
