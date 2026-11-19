import importlib

import pytest


def test_package_version():
    import wikigraph

    assert wikigraph.__version__


@pytest.mark.parametrize("stage", ["ingest", "graph", "search", "evaluation"])
def test_stage_packages_import(stage):
    importlib.import_module(f"wikigraph.{stage}")
