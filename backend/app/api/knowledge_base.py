"""知识库相关 API。

这版接口支持：
1. 新建多个知识库
2. 给指定知识库上传文件
3. 查看知识库文件列表
4. 预览/下载知识库文件
5. 为指定知识库构建向量库
6. 在指定知识库中发起问答
7. 迁移旧知识库元数据
"""

from mimetypes import guess_type

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, PlainTextResponse

from backend.app.loaders.document_loader import load_document_text
from backend.app.rag.qa_service import answer_question
from backend.app.schemas.common import ApiResponse
from backend.app.schemas.knowledge_base import AskRequest, BuildKnowledgeBaseRequest, CreateKnowledgeBaseRequest
from backend.app.services.document_center_service import sync_kb_build_status
from backend.app.services.knowledge_base_service import (
    create_knowledge_base,
    delete_knowledge_base,
    ensure_kb_exists,
    ensure_safe_filename,
    get_kb_file_path,
    list_kb_files,
    list_knowledge_bases,
    migrate_legacy_knowledge_bases,
    update_kb_build_status,
    validate_extension,
)
from backend.app.services.text_splitter_service import split_documents
from backend.app.services.vector_store_service import build_and_save_vectorstore

router = APIRouter()


@router.get("", response_model=ApiResponse)
def get_knowledge_bases():
    """获取全部知识库列表。"""

    return ApiResponse(success=True, message="Knowledge bases fetched successfully", data=list_knowledge_bases())


@router.post("", response_model=ApiResponse)
def create_kb(request: CreateKnowledgeBaseRequest):
    """新建知识库。"""

    data = create_knowledge_base(request.name)
    return ApiResponse(success=True, message="Knowledge base created successfully", data=data)


@router.post("/migrate", response_model=ApiResponse)
def migrate_legacy_kbs():
    """手动触发旧知识库迁移。"""

    data = migrate_legacy_knowledge_bases()
    return ApiResponse(success=True, message="Legacy knowledge bases migrated successfully", data=data)


@router.delete("/{knowledge_base_id}", response_model=ApiResponse)
def remove_kb(knowledge_base_id: str):
    """删除指定知识库及其向量索引。"""

    data = delete_knowledge_base(knowledge_base_id)
    return ApiResponse(success=True, message="Knowledge base deleted successfully", data=data)


@router.get("/{knowledge_base_id}/files", response_model=ApiResponse)
def get_kb_files(knowledge_base_id: str):
    """列出指定知识库下的文件。"""

    return ApiResponse(success=True, message="Knowledge base files fetched successfully", data=list_kb_files(knowledge_base_id))


@router.post("/{knowledge_base_id}/upload", response_model=ApiResponse)
async def upload_document(knowledge_base_id: str, file: UploadFile = File(...)):
    """向指定知识库上传文件。"""

    if not file.filename:
        raise HTTPException(status_code=400, detail="File name is required")

    validate_extension(file.filename)
    save_path = get_kb_file_path_for_upload(knowledge_base_id, file.filename)

    content = await file.read()
    save_path.write_bytes(content)

    return ApiResponse(
        success=True,
        message="File uploaded successfully",
        data={"knowledge_base_id": knowledge_base_id, "file_name": file.filename, "saved_path": str(save_path)},
    )


@router.get("/{knowledge_base_id}/files/{file_name}/preview")
def preview_document_text(knowledge_base_id: str, file_name: str):
    """返回纯文本预览。

    这个接口主要给 txt 或兜底预览使用；更接近原文件的预览请使用 /content。
    """

    path = get_kb_file_path(knowledge_base_id, file_name)
    text = load_document_text(path)
    return PlainTextResponse(text[:20000] or "文件内容为空")


@router.get("/{knowledge_base_id}/files/{file_name}/content")
def preview_document_content(knowledge_base_id: str, file_name: str):
    """以内联方式返回原始文件，供前端 iframe 或 blob 预览。"""

    path = get_kb_file_path(knowledge_base_id, file_name)
    media_type = guess_type(path.name)[0] or "application/octet-stream"
    return FileResponse(
        path=str(path),
        filename=path.name,
        media_type=media_type,
        headers={"Content-Disposition": f'inline; filename="{path.name}"'},
    )


@router.get("/{knowledge_base_id}/files/{file_name}/download")
def download_document(knowledge_base_id: str, file_name: str):
    """下载知识库中的原始文件。"""

    path = get_kb_file_path(knowledge_base_id, file_name)
    return FileResponse(path=str(path), filename=path.name)


@router.post("/build", response_model=ApiResponse)
def build_knowledge_base(request: BuildKnowledgeBaseRequest):
    """构建指定知识库的向量索引。"""

    try:
        update_kb_build_status(request.knowledge_base_id, "构建中")
        sync_kb_build_status(request.knowledge_base_id, "构建中")

        file_paths = []

        if request.file_names:
            for name in request.file_names:
                safe_name = ensure_safe_filename(name)
                path = get_kb_file_path(request.knowledge_base_id, safe_name)
                file_paths.append(path)
        else:
            file_paths = [
                get_kb_file_path(request.knowledge_base_id, item["name"])
                for item in list_kb_files(request.knowledge_base_id)
            ]

        if not file_paths:
            raise HTTPException(status_code=400, detail="No files available to build the knowledge base")

        docs = []
        for path in file_paths:
            text = load_document_text(path)
            if text.strip():
                docs.append({"text": text, "source": path.name})

        if not docs:
            raise HTTPException(status_code=400, detail="All documents are empty")

        split_docs = split_documents(docs)
        result = build_and_save_vectorstore(split_docs, request.knowledge_base_id)
        update_kb_build_status(request.knowledge_base_id, "已完成")
        sync_kb_build_status(request.knowledge_base_id, "已完成")
        return ApiResponse(success=True, message="Knowledge base built successfully", data=result)
    except Exception:
        update_kb_build_status(request.knowledge_base_id, "失败")
        sync_kb_build_status(request.knowledge_base_id, "失败")
        raise


@router.post("/ask", response_model=ApiResponse)
def ask_knowledge_base(request: AskRequest):
    """在指定知识库上执行问答。"""

    result = answer_question(
        knowledge_base_id=request.knowledge_base_id,
        question=request.question,
        top_k=request.top_k,
    )
    return ApiResponse(success=True, message="Question answered successfully", data=result)


def get_kb_file_path_for_upload(knowledge_base_id: str, file_name: str):
    """生成上传目标路径。"""

    from backend.app.config import UPLOAD_DIR

    ensure_kb_exists(knowledge_base_id)
    safe_name = ensure_safe_filename(file_name)
    return UPLOAD_DIR / knowledge_base_id / safe_name
