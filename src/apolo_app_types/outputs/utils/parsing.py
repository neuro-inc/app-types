import typing as t

import click

from apolo_app_types.clients.kube import get_services_by_label


def parse_cli_args(args: list[str]) -> dict[str, t.Any]:
    # Args could be in the form of '--key=value' or '--key value'
    result = {}
    for arg in args:
        if not arg.startswith(("-", "--")):
            print("Don't know how to handle argument:", arg)  # noqa: T201
            continue
        # you can pass any arguments to add_argument
        kv = arg.lstrip("-")
        if " " in kv:
            key, value = kv.split(" ", 1)
        else:
            key, value = kv.split("=", 1)
        result[key] = value
    return result


async def get_service_host_port(match_labels: dict[str, str]) -> tuple[str, str]:
    label_selectors = ",".join(f"{k}={v}" for k, v in match_labels.items())
    get_svc_stdout = await get_services_by_label(label_selectors)
    if not get_svc_stdout["items"]:
        msg = f"Service with labels {label_selectors} not found"
        raise click.ClickException(msg)
    if len(get_svc_stdout["items"]) > 1:
        msg = f"Multiple services with labels {label_selectors} found"
        raise click.ClickException(msg)

    service = get_svc_stdout["items"][0]
    host = f'{service["metadata"]["name"]}.{service["metadata"]["namespace"]}'
    post = str(service["spec"]["ports"][0]["port"])

    return host, post
