from .networking import RestAPI


class OpenAICompatibleEmbeddingsRestAPI(RestAPI):
    endpoint_url: str = "/v1/embeddings"
