import pytest

from apolo_app_types import HuggingFaceModel
from apolo_app_types.app_types import AppType
from apolo_app_types.inputs.args import app_type_to_vals
from apolo_app_types.protocols.common import IngressHttp, Preset
from apolo_app_types.protocols.text_embeddings import TextEmbeddingsInferenceAppInputs

from tests.unit.constants import (
    APP_ID,
    APP_SECRETS_NAME,
)


@pytest.mark.asyncio
async def test_tei_values_generation(setup_clients):
    helm_args, helm_params = await app_type_to_vals(
        input_=TextEmbeddingsInferenceAppInputs(
            preset=Preset(name="cpu-small"),
            ingress_http=IngressHttp(
                clusterName="default",
            ),
            model=HuggingFaceModel(
                model_hf_name="random/name", hf_token="random-token"
            ),
            server_extra_args=[
                "--max-concurrent-requests=512",
                "--max-client-batch-size=16",
            ],
        ),
        apolo_client=setup_clients,
        app_type=AppType.TextEmbeddingsInference,
        app_name="tei-app",
        namespace="default-namespace",
        app_secrets_name=APP_SECRETS_NAME,
        app_id=APP_ID,
    )
    assert helm_params["image"] == {
        "repository": "ghcr.io/huggingface/text-embeddings-inference",
        "tag": "1.7",
    }
    assert helm_params["model"] == {
        "modelHFName": "random/name",
    }
    assert helm_params["env"] == {
        "HUGGING_FACE_HUB_TOKEN": "random-token",
    }
    assert helm_params["serverExtraArgs"] == [
        "--max-concurrent-requests=512",
        "--max-client-batch-size=16",
    ]
