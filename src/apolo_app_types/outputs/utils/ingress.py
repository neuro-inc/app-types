import logging
import typing

from apolo_app_types.clients.kube import get_ingresses_as_dict


logger = logging.getLogger(__name__)


async def get_ingresses(
    match_labels: dict[str, str],
) -> dict[str, list[dict[str, typing.Any]]] | None:
    label_selectors = ",".join(f"{k}={v}" for k, v in match_labels.items())
    get_ing_stdout = await get_ingresses_as_dict(label_selectors)
    if not get_ing_stdout["items"]:
        return None
    if len(get_ing_stdout["items"]) > 1:
        logger.warning(
            "Multiple ingresses found, using label selectors %s", label_selectors
        )

    return get_ing_stdout


async def get_ingress_host_port(
    match_labels: dict[str, str],
) -> tuple[str, int] | None:
    get_ing_stdout = await get_ingresses(match_labels)
    if not get_ing_stdout:
        return None
    ingress = get_ing_stdout["items"][0]
    if len(ingress["spec"]["rules"]) > 1:
        msg = f"Multiple rules in ingress with labels {match_labels} found"
        raise Exception(msg)

    host = ingress["spec"]["rules"][0]["host"]
    return host, 80  # traefik is exposed on 80,443 ports
