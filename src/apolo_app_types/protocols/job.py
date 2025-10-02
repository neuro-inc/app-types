from __future__ import annotations

import typing as t
from enum import StrEnum

from pydantic import ConfigDict, Field

from apolo_app_types.protocols.common import (
    AbstractAppFieldType,
    AppInputs,
    AppOutputs,
    SchemaExtraMetadata,
    SchemaMetaType,
)
from apolo_app_types.protocols.common.k8s import Env
from apolo_app_types.protocols.common.preset import Preset
from apolo_app_types.protocols.common.secrets_ import ApoloSecret
from apolo_app_types.protocols.common.storage import StorageMounts
from apolo_app_types.protocols.mlflow import MLFlowTrackingServerURL


class JobPriority(StrEnum):
    """Job priority levels for resource allocation."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


class JobRestartPolicy(StrEnum):
    """Job restart policy for handling failures."""

    ALWAYS = "always"
    ON_FAILURE = "on-failure"
    NEVER = "never"


class SecretVolume(AbstractAppFieldType):
    """Mount a secret into the container filesystem."""

    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Secret Volume",
            description="Mount a secret into a target path inside the container.",
        ).as_json_schema_extra(),
    )

    src_secret_uri: ApoloSecret = Field(
        json_schema_extra=SchemaExtraMetadata(
            title="Source Secret",
            description="Reference to a secret (e.g., apolo://secret/<path>).",
        ).as_json_schema_extra(),
    )
    dst_path: t.Annotated[
        str,
        Field(
            json_schema_extra=SchemaExtraMetadata(
                title="Destination Path",
                description="Absolute path where the secret will be mounted.",
            ).as_json_schema_extra()
        ),
    ]


class DiskVolume(AbstractAppFieldType):
    """Mount a persistent disk into the container filesystem."""

    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Disk Volume",
            description="Attach a persistent disk to the container at a target path.",
        ).as_json_schema_extra(),
    )

    src_disk_uri: t.Annotated[
        str,
        Field(
            json_schema_extra=SchemaExtraMetadata(
                title="Source Disk URI",
                description="Reference to a disk (e.g., storage://cluster/org/proj/disk).",
            ).as_json_schema_extra()
        ),
    ]
    dst_path: t.Annotated[
        str,
        Field(
            json_schema_extra=SchemaExtraMetadata(
                title="Destination Path",
                description="Absolute path where the disk will be mounted.",
            ).as_json_schema_extra()
        ),
    ]
    read_only: bool = Field(
        default=False,
        json_schema_extra=SchemaExtraMetadata(
            title="Read Only",
            description="Mount the disk as read-only if enabled.",
        ).as_json_schema_extra(),
    )


class JobImageConfig(AbstractAppFieldType):
    """Container image configuration and runtime parameters."""

    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Image Configuration",
            description="Container image, execution parameters, and environment setup.",
        ).as_json_schema_extra(),
    )

    image: t.Annotated[
        str,
        Field(
            json_schema_extra=SchemaExtraMetadata(
                title="Container Image",
                description="OCI image to run (e.g., ghcr.io/org/image:tag).",
            ).as_json_schema_extra()
        ),
    ]

    entrypoint: t.Annotated[
        str,
        Field(
            default="",
            json_schema_extra=SchemaExtraMetadata(
                title="Entrypoint",
                description="Override container "
                "entrypoint. Leave empty to use image default.",
            ).as_json_schema_extra(),
        ),
    ] = ""

    command: t.Annotated[
        str,
        Field(
            default="",
            json_schema_extra=SchemaExtraMetadata(
                title="Command",
                description="Command/args string passed "
                "to the container. Leave empty to use image CMD.",
            ).as_json_schema_extra(),
        ),
    ] = ""

    env: list[Env] = Field(
        default_factory=list,
        json_schema_extra=SchemaExtraMetadata(
            title="Environment Variables",
            description="List of environment variables to inject into the container.",
        ).as_json_schema_extra(),
    )

    secret_env: list[Env] = Field(
        default_factory=list,
        json_schema_extra=SchemaExtraMetadata(
            title="Secret Environment Variables",
            description="Environment variables whose values come from secrets.",
        ).as_json_schema_extra(),
    )

    working_dir: t.Annotated[
        str,
        Field(
            default="",
            json_schema_extra=SchemaExtraMetadata(
                title="Working Directory",
                description="Working directory inside the container (absolute path).",
            ).as_json_schema_extra(),
        ),
    ] = ""


class JobResourcesConfig(AbstractAppFieldType):
    """Resource allocation and compute requirements."""

    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Resources Configuration",
            description="CPU, memory, GPU, and storage resource specifications.",
        ).as_json_schema_extra(),
    )

    preset: Preset = Field(
        json_schema_extra=SchemaExtraMetadata(
            title="Resource Preset",
            description="Select CPU/GPU/memory/storage resources for the job.",
        ).as_json_schema_extra(),
    )

    storage_mounts: StorageMounts | None = Field(
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="Storage Mounts",
            description="Mount object/block filesystems as configured storage.",
        ).as_json_schema_extra(),
    )

    secret_volumes: list[SecretVolume] | None = Field(
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="Secret Volumes",
            description="List of secret volumes to mount inside the container.",
        ).as_json_schema_extra(),
    )

    disk_volumes: list[DiskVolume] | None = Field(
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="Disk Volumes",
            description="List of persistent disk volumes to mount.",
        ).as_json_schema_extra(),
    )


class JobNetworkingConfig(AbstractAppFieldType):
    """Network and storage connectivity configuration."""

    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Networking Configuration",
            description="HTTP endpoints and connectivity settings.",
        ).as_json_schema_extra(),
    )

    http: ContainerHTTPServer | None = Field(
        default=None,
        json_schema_extra=SchemaExtraMetadata(
            title="HTTP Server Configuration",
            description="Expose an HTTP server for health checks or APIs.",
        ).as_json_schema_extra(),
    )


class JobSchedulingConfig(AbstractAppFieldType):
    """Job scheduling, priority, and execution policies."""

    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Scheduling Configuration",
            description="Priority, timeouts, restart policies, and scheduler settings.",
            is_advanced_field=True,
        ).as_json_schema_extra(),
    )

    priority: JobPriority = Field(
        default=JobPriority.NORMAL,
        json_schema_extra=SchemaExtraMetadata(
            title="Job Priority",
            description="Set the scheduling priority: low, normal, or high.",
        ).as_json_schema_extra(),
    )

    scheduler_enabled: bool = Field(
        default=False,
        json_schema_extra=SchemaExtraMetadata(
            title="Scheduler Enabled",
            description="Enable the platform scheduler for queued execution.",
        ).as_json_schema_extra(),
    )

    preemptible_node: bool = Field(
        default=False,
        json_schema_extra=SchemaExtraMetadata(
            title="Preemptible Node",
            description="Allow placement on preemptible nodes (may be evicted).",
        ).as_json_schema_extra(),
    )

    restart_policy: JobRestartPolicy = Field(
        default=JobRestartPolicy.NEVER,
        json_schema_extra=SchemaExtraMetadata(
            title="Restart Policy",
            description="Restart behavior for failed containers.",
        ).as_json_schema_extra(),
    )

    max_run_time_minutes: int = Field(
        default=0,
        json_schema_extra=SchemaExtraMetadata(
            title="Max Runtime (Minutes)",
            description="Maximum allowed runtime in minutes (0 = unlimited).",
        ).as_json_schema_extra(),
    )

    schedule_timeout: float = Field(
        default=0.0,
        json_schema_extra=SchemaExtraMetadata(
            title="Schedule Timeout (Seconds)",
            description="How long to wait for"
            " scheduling before timing out (0 = no timeout).",
        ).as_json_schema_extra(),
    )

    energy_schedule_name: t.Annotated[
        str,
        Field(
            default="",
            json_schema_extra=SchemaExtraMetadata(
                title="Energy Schedule Name",
                description="Optional energy/cost-aware schedule policy name.",
            ).as_json_schema_extra(),
        ),
    ] = ""

    wait_for_jobs_quota: bool = Field(
        default=False,
        json_schema_extra=SchemaExtraMetadata(
            title="Wait for Jobs Quota",
            description="Block submission until sufficient job quota is available.",
        ).as_json_schema_extra(),
    )


class JobAdvancedConfig(AbstractAppFieldType):
    """Advanced runtime configuration and platform integration."""

    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Advanced Configuration",
            description="Security, quotas, configuration injection, "
            "and advanced runtime settings.",
            is_advanced_field=True,
        ).as_json_schema_extra(),
    )

    pass_config: bool = Field(
        default=False,
        json_schema_extra=SchemaExtraMetadata(
            title="Pass Config",
            description="Inject platform/application config into the container.",
        ).as_json_schema_extra(),
    )

    privileged: bool = Field(
        default=False,
        json_schema_extra=SchemaExtraMetadata(
            title="Privileged Mode",
            description="Run the container in privileged mode if the cluster "
            "configuration permits. Contact the system administrators to "
            "confirm whether this feature is enabled in this cluster.",
        ).as_json_schema_extra(),
    )


class JobMetadataConfig(AbstractAppFieldType):
    """Job identification and organizational metadata."""

    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Metadata Configuration",
            description="Job name, description, tags, and organizational information.",
        ).as_json_schema_extra(),
    )

    name: t.Annotated[
        str,
        Field(
            default="",
            pattern=r"^$|^[a-z](?:-?[a-z0-9])*$",
            json_schema_extra=SchemaExtraMetadata(
                title="Job Name",
                description="Job name used for public URL. "
                "Must be lowercase letters, digits, and hyphens only.",
            ).as_json_schema_extra(),
        ),
    ] = ""

    description: t.Annotated[
        str,
        Field(
            default="",
            json_schema_extra=SchemaExtraMetadata(
                title="Job Description",
                description="Optional description for the job purpose.",
            ).as_json_schema_extra(),
        ),
    ] = ""

    tags: list[str] = Field(
        default_factory=list,
        json_schema_extra=SchemaExtraMetadata(
            title="Job Tags",
            description="Set arbitrary tags/labels to help categorize the job.",
        ).as_json_schema_extra(),
    )


class ContainerHTTPServer(AbstractAppFieldType):
    """HTTP server configuration exposed by the container."""

    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="HTTP Server",
            description="Expose an HTTP server from the container for health or API.",
        ).as_json_schema_extra(),
    )

    port: int = Field(
        json_schema_extra=SchemaExtraMetadata(
            title="Port",
            description="Container TCP port to expose for the HTTP server.",
        ).as_json_schema_extra(),
    )
    health_check_path: (
        t.Annotated[
            str,
            Field(
                json_schema_extra=SchemaExtraMetadata(
                    title="Health Check Path",
                    description="Optional HTTP path used for "
                    "readiness/liveness checks (e.g., /healthz).",
                ).as_json_schema_extra()
            ),
        ]
        | None
    ) = None
    requires_auth: bool = Field(
        default=False,
        json_schema_extra=SchemaExtraMetadata(
            title="Requires Auth",
            description="If enabled, requests to this server must be authenticated.",
        ).as_json_schema_extra(),
    )


class JobIntegrationsConfig(AbstractAppFieldType):
    """Integrations configuration."""

    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Integrations",
            description="Integrate your job with applications.",
            is_advanced_field=True,
        ).as_json_schema_extra(),
    )

    mlflow_integration: MLFlowTrackingServerURL = Field(
        default=MLFlowTrackingServerURL(),
        json_schema_extra=SchemaExtraMetadata(
            title="MLFlow Integration",
            description=(
                "Preconfigure the job to access the MLflow server. "
                "If enabled, the job will receive the MLflow tracking server URL"
                "as the MLFLOW_TRACKING_URI environment variable and will be "
                "authorized to access it."
            ),
            meta_type=SchemaMetaType.INTEGRATION,
        ).as_json_schema_extra(),
    )


class JobAppInput(AppInputs):
    """Top-level configuration for a generic batch/Job container."""

    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Job Configuration",
            description="Configure the container image, "
            "command, resources, mounts, and runtime policy.",
        ).as_json_schema_extra(),
    )

    metadata: JobMetadataConfig = Field(
        default_factory=JobMetadataConfig,
    )

    image: JobImageConfig

    resources: JobResourcesConfig

    networking: JobNetworkingConfig = Field(
        default_factory=JobNetworkingConfig,
    )

    integrations: JobIntegrationsConfig = Field(
        default_factory=JobIntegrationsConfig,
    )

    scheduling: JobSchedulingConfig = Field(
        default_factory=JobSchedulingConfig,
    )

    advanced: JobAdvancedConfig = Field(
        default_factory=JobAdvancedConfig,
    )


class JobAppOutput(AppOutputs):
    """Outputs produced after job submission/execution."""

    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra=SchemaExtraMetadata(
            title="Job Outputs",
            description="Runtime identifiers and status emitted by the platform.",
        ).as_json_schema_extra(),
    )

    job_id: (
        t.Annotated[
            str,
            Field(
                json_schema_extra=SchemaExtraMetadata(
                    title="Job ID",
                    description="Unique identifier assigned to the submitted job.",
                ).as_json_schema_extra()
            ),
        ]
        | None
    ) = None

    job_status: (
        t.Annotated[
            str,
            Field(
                json_schema_extra=SchemaExtraMetadata(
                    title="Job Status",
                    description="Current status (e.g., "
                    "Pending, Running, Succeeded, Failed).",
                ).as_json_schema_extra()
            ),
        ]
        | None
    ) = None

    job_uri: (
        t.Annotated[
            str,
            Field(
                json_schema_extra=SchemaExtraMetadata(
                    title="Job URI",
                    description="Canonical URI to locate or reference this job.",
                ).as_json_schema_extra()
            ),
        ]
        | None
    ) = None
