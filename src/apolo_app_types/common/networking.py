from pydantic import BaseModel, Field


class HttpApi(BaseModel):
    host: str = Field(..., description="The host of the HTTP endpoint.")
    port: int = Field(..., description="The port of the HTTP endpoint.")
    protocol: str = Field("http", description="The protocol to use, e.g., http or https.")
    timeout: float | None = Field(default=30.0, description="Connection timeout in seconds.")
    base_path: str = ""


class GraphQLAPI(HttpApi):
    pass


class RestAPI(HttpApi):
    pass


class GrpcAPI(HttpApi):
    pass
