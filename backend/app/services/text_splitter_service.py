from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from backend.app.config import settings


def split_documents(raw_docs: list[dict]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", "。", "；", ";", " "],
    )

    final_docs = []
    for item in raw_docs:
        chunks = splitter.split_text(item["text"])
        for index, chunk in enumerate(chunks):
            final_docs.append(
                Document(
                    page_content=chunk,
                    metadata={"source": item["source"], "chunk_index": index},
                )
            )
    return final_docs
