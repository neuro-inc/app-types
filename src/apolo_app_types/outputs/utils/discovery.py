import importlib
import inspect
import logging
import pkgutil

from apolo_app_types.outputs.base import BaseAppOutputsProcessor


logger = logging.getLogger(__name__)


def load_app_postprocessor(
    app_id: str,
    apolo_app_package_prefix: str = "apolo_apps_",
) -> type[BaseAppOutputsProcessor] | None:
    package = None
    for _, name, _ in pkgutil.iter_modules():
        if not name.startswith(apolo_app_package_prefix):
            continue
        candidate = importlib.import_module(name)
        logger.debug("Found %s at %s", candidate.__name__, candidate.__file__)
        package_app_id = getattr(candidate, "APOLO_APP_ID", None)
        if package_app_id == app_id:
            logger.info("Found %s in %s", app_id, candidate.__name__)
            package = candidate
            break

    if not package:
        logger.warning("App %s not found", app_id)
        return None

    for _, klass in inspect.getmembers(package, inspect.isclass):
        if (
            issubclass(klass, BaseAppOutputsProcessor)
            and klass is not BaseAppOutputsProcessor
        ):
            logger.info("Found output processor %s for %s", klass, app_id)
            return klass

    logger.warning("Output processor not found for %s", app_id)
    return None
