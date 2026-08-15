import pytest


pytest.importorskip("pydantic")

from pydantic import ValidationError

from apolo_app_types.protocols.common.k8s import IngressPathTypeEnum, Port


@pytest.mark.parametrize("path_type", list(IngressPathTypeEnum))
@pytest.mark.parametrize(
    "path",
    [
        "/",
        "/api/v1",
        "/with%20encoded",
        "/tilde~._-slash/",
    ],
)
def test_literal_paths_valid_for_all_path_types(path, path_type):
    assert Port(path=path, path_type=path_type).path == path


@pytest.mark.parametrize(
    "path",
    [
        "",  # min_length
        "/has space",  # whitespace guard
        "/has\ttab",
    ],
)
def test_whitespace_and_empty_rejected_for_all_path_types(path):
    for path_type in IngressPathTypeEnum:
        with pytest.raises(ValidationError):
            Port(path=path, path_type=path_type)


@pytest.mark.parametrize(
    "path_type", [IngressPathTypeEnum.PREFIX, IngressPathTypeEnum.EXACT]
)
@pytest.mark.parametrize(
    "path",
    [
        "api",  # missing leading slash
        "/products?query=1",  # query string
        "^/products$",  # regex metachars not allowed for literal paths
    ],
)
def test_literal_path_types_reject_non_literal(path, path_type):
    with pytest.raises(ValidationError):
        Port(path=path, path_type=path_type)


@pytest.mark.parametrize(
    "path",
    [
        "^/products/(shoes|socks)/[0-9]+$",
        "(?i)^/products",
        r"\.(jpeg|jpg|png)$",
        "/plain/path",
    ],
)
def test_implementation_specific_accepts_valid_regex(path):
    port = Port(path=path, path_type=IngressPathTypeEnum.IMPLEMENTATION_SPECIFIC)
    assert port.path == path


def test_implementation_specific_rejects_invalid_regex():
    with pytest.raises(ValidationError):
        Port(
            path="^/products/(unbalanced",
            path_type=IngressPathTypeEnum.IMPLEMENTATION_SPECIFIC,
        )
