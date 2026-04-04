"""向量库构建与检索服务。"""

from pathlib import Path

from langchain_community.vectorstores import FAISS

from backend.app.services.embedding_service import get_embeddings
from backend.app.services.knowledge_base_service import get_vectorstore_path


def build_and_save_vectorstore(documents: list, knowledge_base_id: str):
    """把切分后的文档写入指定知识库的 FAISS 索引。"""

    index_path = get_vectorstore_path(knowledge_base_id)
    embeddings = get_embeddings()
    vectorstore = FAISS.from_documents(documents, embeddings)
    vectorstore.save_local(str(index_path))

    unique_sources = sorted({doc.metadata.get("source", "") for doc in documents})
    return {
        "knowledge_base_id": knowledge_base_id,
        "document_count": len(documents),
        "sources": unique_sources,
        "vectorstore_path": str(index_path),
    }


def load_vectorstore(knowledge_base_id: str) -> FAISS:
    """加载指定知识库的向量索引。"""

    index_path = get_vectorstore_path(knowledge_base_id)
    if not Path(str(index_path)).exists():
        raise FileNotFoundError("Vector store does not exist. Build it first.")

    embeddings = get_embeddings()
    return FAISS.load_local(
        str(index_path),
        embeddings,
        allow_dangerous_deserialization=True,
    )


def search_similar_chunks(query: str, top_k: int, knowledge_base_id: str):
    """在目标知识库内执行相似度检索。"""

    vectorstore = load_vectorstore(knowledge_base_id)
    return vectorstore.similarity_search_with_score(query, k=top_k)
