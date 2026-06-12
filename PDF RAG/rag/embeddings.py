"""Embeddings and FAISS vector store management."""
import os
from langchain_community.vectorstores import FAISS

_EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


class SelfHealingEmbeddings:
    """
    Embeddings wrapper that attempts cloud-based API inference first (to save server memory),
    but automatically falls back to local offline embeddings if a network error occurs.
    """
    def __init__(self, hf_token: str, model_name: str):
        self.hf_token = hf_token
        self.model_name = model_name
        self._local_embeddings = None
        self._cloud_embeddings = None
        
        if hf_token:
            try:
                from langchain_community.embeddings import HuggingFaceInferenceAPIEmbeddings
                self._cloud_embeddings = HuggingFaceInferenceAPIEmbeddings(
                    api_key=hf_token,
                    model_name=model_name
                )
            except Exception:
                pass

    def _get_local(self):
        if os.environ.get("RENDER") == "true" or os.environ.get("render") == "true":
            raise RuntimeError(
                "Hugging Face API connection failed. Local offline embeddings fallback is disabled "
                "on Render to prevent 512MB memory limit crashes. Please verify that your HUGGINGFACE_API_KEY "
                "environment variable is configured correctly on Render."
            )
        if not self._local_embeddings:
            import traceback
            import sys
            print("[DEBUG] Python path:", sys.path)
            try:
                print("[DEBUG] Attempting manual import of sentence_transformers...")
                import sentence_transformers
                print("[DEBUG] sentence_transformers imported successfully!")
            except BaseException as e:
                print("[ERROR] Manual import of sentence_transformers failed:", str(e))
                traceback.print_exc()
            from langchain_community.embeddings import HuggingFaceEmbeddings
            self._local_embeddings = HuggingFaceEmbeddings(model_name=self.model_name)
        return self._local_embeddings

    def embed_documents(self, texts):
        if self._cloud_embeddings:
            try:
                return self._cloud_embeddings.embed_documents(texts)
            except Exception as e:
                print(f"[WARN] Cloud embeddings API failed: {e}. Falling back to local offline embeddings...")
                self._cloud_embeddings = None  # Disable cloud for the rest of this session
        return self._get_local().embed_documents(texts)

    def embed_query(self, text):
        if self._cloud_embeddings:
            try:
                return self._cloud_embeddings.embed_query(text)
            except Exception as e:
                print(f"[WARN] Cloud embeddings API failed: {e}. Falling back to local offline embeddings...")
                self._cloud_embeddings = None  # Disable cloud for the rest of this session
        return self._get_local().embed_query(text)


def get_embeddings():
    hf_token = os.environ.get("HUGGINGFACE_API_KEY") or os.environ.get("HF_TOKEN")
    return SelfHealingEmbeddings(hf_token, _EMBED_MODEL)


def build_vectorstore(chunks):
    """Build FAISS vector store from document chunks."""
    embeddings = get_embeddings()
    vectorstore = FAISS.from_documents(chunks, embeddings)
    return vectorstore


def get_retriever(vectorstore, k: int = 5):
    return vectorstore.as_retriever(search_kwargs={"k": k})
