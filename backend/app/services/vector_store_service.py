from pathlib import Path

from langchain_community.vectorstores import FAISS

from backend.app.config import VECTORSTORE_DIR
from backend.app.services.embedding_service import get_embeddings

INDEX_PATH = VECTORSTORE_DIR / "kb_index"


def build_and_save_vectorstore(documents: list):
    embeddings = get_embeddings()
    vectorstore = FAISS.from_documents(documents, embeddings)
    vectorstore.save_local(str(INDEX_PATH))

    unique_sources = sorted({doc.metadata.get("source", "") for doc in documents})
    return {
        "document_count": len(documents),
        "sources": unique_sources,
        "vectorstore_path": str(INDEX_PATH),
    }


def load_vectorstore() -> FAISS:
    if not Path(str(INDEX_PATH)).exists():
        raise FileNotFoundError("Vector store does not exist. Build it first.")

    embeddings = get_embeddings()
    return FAISS.load_local(
        str(INDEX_PATH),
        embeddings,
        allow_dangerous_deserialization=True,
    )


def search_similar_chunks(query: str, top_k: int):
    vectorstore = load_vectorstore()
    return vectorstore.similarity_search_with_score(query, k=top_k)
