import typing as t

from apolo_app_types.protocols.common.health_check import (
    HealthCheck,
    HealthCheckProbesConfig,
    ProbeType,
)


def get_probe_values(config: HealthCheck) -> dict[str, t.Any]:
    values: dict[str, t.Any] = {
        "initialDelaySeconds": config.initial_delay,
        "timeoutSeconds": config.timeout,
        "periodSeconds": config.period,
        "failureThreshold": config.failure_threshold,
    }
    if config.health_check_config.probe_type == ProbeType.TCP:
        values["tcpSocket"] = {"port": config.health_check_config.port}
    elif config.health_check_config.probe_type == ProbeType.HTTP:
        values["httpGet"] = {
            "path": config.health_check_config.path,
            "port": config.health_check_config.port,
        }
        if config.health_check_config.http_headers:
            values["httpGet"]["httpHeaders"] = [
                {"name": k, "value": v}
                for k, v in config.health_check_config.http_headers.items()
            ]
    elif config.health_check_config.probe_type == ProbeType.GRPC:
        values["grpc"] = {
            "port": config.health_check_config.port,
            "service": config.health_check_config.service,
        }
    elif config.health_check_config.probe_type == ProbeType.EXEC:
        values["exec"] = {
            "command": config.health_check_config.command,
        }
    else:
        err = f"Unsupported probe type: {config.health_check_config.probe_type}"
        raise ValueError(err)
    return values


def get_custom_deployment_health_check_values(
    health_checks: HealthCheckProbesConfig | None,
) -> dict[str, t.Any]:
    if not health_checks:
        return {}
    values: dict[str, t.Any] = {"health_checks": {}}
    if health_checks.startup:
        values["health_checks"]["startupProbe"] = get_probe_values(
            health_checks.startup
        )

    if health_checks.liveness:
        values["health_checks"]["livenessProbe"] = get_probe_values(
            health_checks.liveness
        )

    if health_checks.readiness:
        values["health_checks"]["readinessProbe"] = get_probe_values(
            health_checks.readiness
        )
    return values
