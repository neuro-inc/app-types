import importlib
import inspect
import logging
import pkgutil
import typing as t

from apolo_app_types import AppInputs
from apolo_app_types.helm.apps.base import BaseChartValueProcessor
from apolo_app_types.outputs.base import BaseAppOutputsProcessor


logger = logging.getLogger(__name__)


def load_app_component(
    app_id: str,
    component_base_type: type[t.Any],
    exact_type_name: str | None = None,
    apolo_app_package_prefix: str = "apolo_apps_",
) -> type[t.Any] | None:
    discovered_plugins = {}
    for _finder, name, _ispkg in pkgutil.iter_modules():
        if name.startswith(apolo_app_package_prefix):
            try:
                candidate = importlib.import_module(name)
                candidate_app_id = candidate.APOLO_APP_ID
                discovered_plugins[candidate_app_id] = candidate
            except (ImportError, AttributeError) as e:
                msg = f"Failed to import {name}: {e}"
                logger.warning(msg)
    module = discovered_plugins.get(app_id)

    if not module:
        return None
    msg = f"Found {module} at {module.__file__} for {app_id}"
    logging.info(msg)

    results = []
    for _, obj in inspect.getmembers(module, inspect.isclass):
        if (
            issubclass(obj, component_base_type)
            and obj is not component_base_type
            and (not exact_type_name or obj.__name__ == exact_type_name)
        ):
            msg = f"Found {obj} for {app_id}"
            logging.info(msg)
            results.append(obj)

    if not results:
        return None
    if len(results) > 1:
        msg = f"Multiple components found for {app_id}: {results}"
        raise ValueError(msg)
    return results[0]


def load_app_postprocessor(
    app_id: str,
    exact_type_name: str | None = None,
    apolo_app_package_prefix: str = "apolo_apps_",
) -> type[BaseAppOutputsProcessor] | None:  # type: ignore
    return load_app_component(
        app_id, BaseAppOutputsProcessor, exact_type_name, apolo_app_package_prefix
    )


def load_app_preprocessor(
    app_id: str,
    exact_type_name: str | None = None,
    apolo_app_package_prefix: str = "apolo_apps_",
) -> type[BaseChartValueProcessor] | None:  # type: ignore
    return load_app_component(
        app_id, BaseChartValueProcessor, exact_type_name, apolo_app_package_prefix
    )


def load_app_inputs(
    app_id: str,
    exact_type_name: str | None = None,
    apolo_app_package_prefix: str = "apolo_apps_",
) -> type[AppInputs] | None:
    return load_app_component(
        app_id, AppInputs, exact_type_name, apolo_app_package_prefix
    )
