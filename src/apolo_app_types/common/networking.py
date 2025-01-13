from pydantic import BaseModel, Field
from typing_extensions import Literal


class HttpApi(BaseModel):
    host: str = Field(..., description="The host of the HTTP endpoint.")
    port: int = Field(default=80, description="The port of the HTTP endpoint.")
    protocol: str = Field(
        "http", description="The protocol to use, e.g., http or https."
    )
    timeout: float | None = Field(
        default=30.0, description="Connection timeout in seconds."
    )
    base_path: str = ""


class GraphQLAPI(HttpApi):
    api_type: Literal["graphql"] = "graphql"


class RestAPI(HttpApi):
    api_type: Literal["rest"] = "rest"


class GrpcAPI(HttpApi):
    api_type: Literal["grpc"] = "grpc"
