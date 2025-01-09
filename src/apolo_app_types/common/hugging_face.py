from pydantic import BaseModel, Field


class HuggingFaceModel(BaseModel):
    modelHFName: str = Field(  # noqa: N815
        ...,
        description="The name of the Hugging Face model.",
        title="Hugging Face Model Name",
    )
    modelFiles: str | None = Field(  # noqa: N815
        None, description="The path to the model files.", title="Model Files"
    )
