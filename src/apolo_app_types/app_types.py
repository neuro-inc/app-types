import enum


class AppType(enum.StrEnum):
    PostgreSQL = "postgresql"
    TextEmbeddingsInference = "text-embeddings-inference"
    LLMInference = "llm-inference"
    PrivateGPT = "private-gpt"
    Dify = "dify"
    StableDiffusion = "stable-diffusion"
    Weaviate = "weaviate"
    LightRAG = "lightrag"
    Fooocus = "fooocus"
    Jupyter = "jupyter"
    VSCode = "vscode"
    Pycharm = "pycharm"
    MLFlow = "mlflow"
    Shell = "shell"
    ApoloDeploy = "apolo-deploy"
    DockerHub = "dockerhub"
    HuggingFaceCache = "huggingface-cache"
    CustomDeployment = "custom-deployment"
    ServiceDeployment = "service-deployment"
    SparkJob = "spark-job"
    Superset = "superset"
    OpenWebUI = "openwebui"
    Launchpad = "launchpad"

    # bundles
    Llama4 = "llama4"
    DeepSeek = "deepseek"
    Mistral = "mistral"

    def __repr__(self) -> str:
        return str(self)

    def is_appless(self) -> bool:
        return self in {
            AppType.HuggingFaceCache,
        }
