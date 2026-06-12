"""Embeddings and FAISS vector store management."""
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings


_EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def get_embeddings():
    return HuggingFaceEmbeddings(model_name=_EMBED_MODEL)


def build_vectorstore(chunks):
    """Build FAISS vector store from document chunks."""
    embeddings = get_embeddings()
    vectorstore = FAISS.from_documents(chunks, embeddings)
    return vectorstore


def get_retriever(vectorstore, k: int = 5):
    return vectorstore.as_retriever(search_kwargs={"k": k})
