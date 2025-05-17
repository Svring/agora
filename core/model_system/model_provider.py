from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama


def get_sealos_model(model_name: str):
    return ChatOpenAI(
        model=model_name,
        base_url="https://aiproxy.usw.sealos.io/v1",
        api_key="sk-Yx2FiiiPuF9QS4CivU4Wqfr6SdtYaBgOJSeba9NqqRLEYicU",
    )


def get_ollama_model(model_name: str):
    return ChatOllama(
        model=model_name,
        base_url="http://localhost:11434",
    )
