import importlib.util
import sys
import types
from pathlib import Path
from urllib.parse import quote

import pytest


pytest.importorskip("pydantic")

# Prepare a fake 'apolo_app_types.protocols.common' module to satisfy
# imports performed by resp_api.py without importing the package
# top-level, which may import modules incompatible with the test
# interpreter during collection.
repo_root = Path(__file__).resolve().parents[3]
common_mod_name = "apolo_app_types.protocols.common"
if common_mod_name not in sys.modules:
    common_mod = types.ModuleType(common_mod_name)
    import pydantic

    # Use pydantic.BaseModel as a stand-in for AbstractAppFieldType so
    # RESPApi (a pydantic model) can be instantiated normally.
    common_mod.AbstractAppFieldType = pydantic.BaseModel

    class ApoloSecret(pydantic.BaseModel):
        key: str

    common_mod.ApoloSecret = ApoloSecret

    # Register minimal package modules in sys.modules so the import
    # statements inside resp_api.py resolve to our stand-ins.
    sys.modules["apolo_app_types"] = types.ModuleType("apolo_app_types")
    sys.modules["apolo_app_types.protocols"] = types.ModuleType(
        "apolo_app_types.protocols"
    )
    sys.modules[common_mod_name] = common_mod

# Load resp_api module directly from the src tree
resp_api_path = repo_root / "src" / "apolo_app_types" / "protocols" / "resp_api.py"
spec = importlib.util.spec_from_file_location("tests.resp_api", str(resp_api_path))
resp_mod = importlib.util.module_from_spec(spec)
loader = spec.loader
assert loader is not None
loader.exec_module(resp_mod)

RESPApi = resp_mod.RESPApi
ApoloSecret = sys.modules[common_mod_name].ApoloSecret


def test_no_credentials():
    r = RESPApi(host="localhost", port=6379)
    assert r.resp_uri == "redis://localhost:6379"


def test_plain_password_encoding_and_basepath():
    r = RESPApi(
        host="localhost", port=6379, user="u", password="p@ss:word", base_path="0"
    )
    expected_pw = quote("p@ss:word", safe="")
    assert r.resp_uri == f"redis://u:{expected_pw}@localhost:6379/0"


def test_secret_placeholder_encoded():
    secret = ApoloSecret(key="my-secret-key")
    r = RESPApi(host="redis", port=6379, user="u", password=secret, base_path="/cache")
    pw_text = f"<secret:{secret.key}>"
    pw_enc = quote(pw_text, safe="")
    assert r.resp_uri == f"redis://u:{pw_enc}@redis:6379/cache"


def test_scheme_normalization():
    r1 = RESPApi(scheme="redis", host="redis", port=6379)
    r2 = RESPApi(scheme="redis://", host="redis", port=6379)
    assert r1.resp_uri == "redis://redis:6379"
    assert r2.resp_uri == "redis://redis:6379"
