"""Embeddings and FAISS vector store management."""
import os
from langchain_community.vectorstores import FAISS

_EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def get_embeddings():
    # Check if a Hugging Face API key is configured in env
    hf_token = os.environ.get("HUGGINGFACE_API_KEY") or os.environ.get("HF_TOKEN")
    if hf_token:
        # Runs embeddings in the cloud (0MB local RAM required)
        from langchain_community.embeddings import HuggingFaceInferenceAPIEmbeddings
        return HuggingFaceInferenceAPIEmbeddings(
            api_key=hf_token,
            model_name=_EMBED_MODEL
        )
    else:
        # Fallback to local model execution
        from langchain_community.embeddings import HuggingFaceEmbeddings
        return HuggingFaceEmbeddings(model_name=_EMBED_MODEL)


def build_vectorstore(chunks):
    """Build FAISS vector store from document chunks."""
    embeddings = get_embeddings()
    vectorstore = FAISS.from_documents(chunks, embeddings)
    return vectorstore


def get_retriever(vectorstore, k: int = 5):
    return vectorstore.as_retriever(search_kwargs={"k": k})
