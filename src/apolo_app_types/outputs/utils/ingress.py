import click

from apolo_app_types.utils.kube import get_ingresses_as_dict


async def get_ingress_host_port(
    match_labels: dict[str, str],
) -> tuple[str, str] | None:
    label_selectors = ",".join(f"{k}={v}" for k, v in match_labels.items())
    get_ing_stdout = await get_ingresses_as_dict(label_selectors)
    if not get_ing_stdout["items"]:
        return None
    if len(get_ing_stdout["items"]) > 1:
        msg = f"Multiple ingresses with labels {label_selectors} found"
        raise click.ClickException(msg)

    ingress = get_ing_stdout["items"][0]
    if len(ingress["spec"]["rules"]) > 1:
        msg = f"Multiple rules in ingress with labels {label_selectors} found"
        raise click.ClickException(msg)

    host = ingress["spec"]["rules"][0]["host"]
    return host, "80"  # traefik is exposed on 80,443 ports
