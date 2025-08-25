import contextlib
import importlib
import inspect
import json
import logging
import sys
import typing as t
from pathlib import Path

from apolo_app_types import AppInputs, AppOutputs


APOLO_APP_TYPE_ATTR_NAME = "APOLO_APP_TYPE"

logger = logging.getLogger(__name__)


def dump_schema_type(
    app_package_path: Path,
    expected_app_type_name: str,
    exact_type_name: str,
    output_path: Path,
) -> None:
    if not app_package_path.exists():
        msg = f"Package path {app_package_path} does not exist"
        raise ValueError(msg)
    if not (app_package_path / "__init__.py").is_file():
        msg = f"Package path {app_package_path} does not contain __init__.py"
        raise ValueError(msg)

    @contextlib.contextmanager
    def patch_path_maybe(package_path: Path) -> t.Generator[None, None, None]:
        should_patch_path = str(package_path.parent) not in sys.path
        if should_patch_path:
            sys.path.append(str(package_path.parent))
        yield
        if should_patch_path:
            sys.path.remove(str(package_path.parent))

    with patch_path_maybe(app_package_path):
        package = importlib.import_module(app_package_path.name)

    app_type = getattr(package, APOLO_APP_TYPE_ATTR_NAME, "")
    if app_type != expected_app_type_name:
        msg = (
            f"Module {app_package_path}/__init__.py has {app_type=} "
            f"but expected {expected_app_type_name}"
        )
        raise ValueError(msg)

    cls = None
    for cls_name, cls in inspect.getmembers(package, inspect.isclass):
        if issubclass(cls, AppInputs | AppOutputs) and cls_name == exact_type_name:
            msg = f"Found {cls_name} for {app_type}"
            logger.info(msg)
            break
    if not cls:
        msg = f"No {exact_type_name} found for {app_type}"
        logger.error(msg)
        raise ValueError(msg)

    schema = cls.model_json_schema()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(schema, indent=2) + "\n")
    msg = f"Wrote schema to {output_path}"
    logger.info(msg)
