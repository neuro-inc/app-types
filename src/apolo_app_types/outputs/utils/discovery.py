import importlib
import inspect
import logging
import pkgutil
import typing as t

from apolo_app_types import AppInputs
from apolo_app_types.helm.apps.base import BaseChartValueProcessor
from apolo_app_types.outputs.base import BaseAppOutputsProcessor


logger = logging.getLogger(__name__)
APOLO_APP_PACKAGE_PREFIX = "apolo_apps_"


def load_app_component(
    app_type: str,
    package_name: str,
    component_base_type: type[t.Any],
    exact_type_name: str | None = None,
) -> type[t.Any] | None:
    discovered_plugins = {}
    for _finder, name, _ispkg in pkgutil.iter_modules():
        if name == package_name:
            try:
                candidate = importlib.import_module(name)
                discovered_plugins[app_type] = candidate
            except (ImportError, AttributeError) as e:
                msg = f"Failed to import {name}: {e}"
                logger.warning(msg)
    module = discovered_plugins.get(app_type)

    if not module:
        return None
    msg = f"Found {module} at {module.__file__} for {app_type}"
    logging.info(msg)

    results = []
    for name, obj in inspect.getmembers(module, inspect.isclass):
        if (
            issubclass(obj, component_base_type)
            and obj is not component_base_type
            and (not exact_type_name or name == exact_type_name)
        ):
            msg = f"Found {obj} for {app_type}"
            logging.info(msg)
            results.append(obj)

    if not results:
        return None
    if len(results) > 1:
        msg = f"Multiple components found for {app_type}: {results}"
        raise ValueError(msg)
    return results[0]


def load_app_postprocessor(
    app_type: str,
    package_name: str,
    exact_type_name: str | None = None,
) -> type[BaseAppOutputsProcessor] | None:  # type: ignore
    return load_app_component(
        app_type, package_name, BaseAppOutputsProcessor, exact_type_name
    )


def load_app_preprocessor(
    app_type: str,
    package_name: str,
    exact_type_name: str | None = None,
) -> type[BaseChartValueProcessor] | None:  # type: ignore
    return load_app_component(
        app_type, package_name, BaseChartValueProcessor, exact_type_name
    )


def load_app_inputs(
    app_type: str,
    package_name: str,
    exact_type_name: str | None = None,
) -> type[AppInputs] | None:
    return load_app_component(app_type, package_name, AppInputs, exact_type_name)
