import logging
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
from fastapi import APIRouter, Header
from configuration import OKTAConfig, SSTDConfig
from fastapi import Depends, HTTPException, Query, Path
from utilities.llm_manager import get_vector_db, get_custom_vector_db
from models.request_response_models import KBCreateRequest
import utilities.pg_sql_db_util as db_util
import utilities.sol_std_db_util as std_db_util
from utilities.token_validator import validate_token
from agno.document.reader.pdf_reader import PDFUrlReader
from agno.document.reader.website_reader import WebsiteReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from agno.document import Document as AgnoDocument
from langchain_core.documents import Document as LangDocument
from services.knowledgebase_service import (load_code_files, clone_repo, 
    delete_temp_repository, convert_langchain_to_agno, 
    remove_duplicate_doc, convert_agno_to_langchain)
# from agno.knowledge.s3 import S3KnowledgeBase

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/create")
def create_kb(req: KBCreateRequest, user_id: str, authorization: Optional[str] = Header(None)):

    validate_token(
        bearer_token=authorization,
        metadata=OKTAConfig.OKTA_JWT_OAUTH_CONFIG,
        okta_enable=OKTAConfig.OKTA_ENABLED,
        user_id=user_id
    )

    custom_vector_db = get_custom_vector_db(schema=SSTDConfig.SSTD_SCHEMA, table_name=SSTDConfig.KB_TABLE)
    kb_filters = {
        "kb_name":req.name, 
        "user_id":user_id
    }

    if req.type == "GITHUB":
        if not req.repo_url:
            raise HTTPException(status_code=400, detail="Repository URL is required")
        
        try:
            clone_path = None
            clone_path, repo_name = clone_repo(repo_url=req.repo_url, access_token=req.git_access_token, branch_name=req.repo_branch)
            lang_documents = load_code_files(clone_path=clone_path, extension_list=req.ext_list)
            agno_documents = convert_langchain_to_agno(lang_documents, repo_name)
            
            if not custom_vector_db.exists():
                custom_vector_db.create()

            custom_vector_db.upsert(
                remove_duplicate_doc(agno_documents),
                filters=kb_filters, 
                batch_size=1000
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
        finally:
            if clone_path:
                delete_temp_repository(clone_path=clone_path)

    elif req.type == "PDF_URL":
        if not req.urls:
            raise HTTPException(status_code=400, detail="`urls` is required for pdf_url")
        
        consolidated_agno_docs: List[AgnoDocument] = []
        for url in req.urls:
            agno_docs = PDFUrlReader().read(url) # Agno Docs without Embeddings
            langchain_docs = convert_agno_to_langchain(agno_docs) # Generates Embeddings in Bulk
            agno_documents = convert_langchain_to_agno(langchain_docs, req.name) # Agno Docs with Embeddings
            consolidated_agno_docs.extend(agno_documents)
        
        if not custom_vector_db.exists():
            custom_vector_db.create()

        custom_vector_db.upsert(
            remove_duplicate_doc(consolidated_agno_docs),
            filters=kb_filters, 
            batch_size=1000
        )

    elif req.type == "LOCAL":
        if not req.local_files:
            raise HTTPException(status_code=400, detail="local file content is required")

        file_docs_map = {
            file.filename: [LangDocument(page_content=file.content, metadata={"filename": file.filename})]
            for file in req.local_files
        }

        consolidated_agno_docs: List[AgnoDocument] = []
        for filename, lang_docs in file_docs_map.items():
            document_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=200)
            document_chunks = document_splitter.split_documents(lang_docs)
            agno_docs = convert_langchain_to_agno(document_chunks, name=filename)
            consolidated_agno_docs.extend(agno_docs)

        if not custom_vector_db.exists():
            custom_vector_db.create()

        custom_vector_db.upsert(
            remove_duplicate_doc(consolidated_agno_docs),
            filters=kb_filters, 
            batch_size=1000
        )

    elif req.type == "WEBSITE":
        if not req.urls:
            raise HTTPException(status_code=400, detail="`urls` is required for website")
        
        consolidated_agno_docs: List[AgnoDocument] = []
        for url in req.urls:
            agno_docs = WebsiteReader().read(url) # Agno Docs without Embeddings
            langchain_docs = convert_agno_to_langchain(agno_docs) # Generates Embeddings in Bulk
            agno_documents = convert_langchain_to_agno(langchain_docs, req.name) # Agno Docs with Embeddings
            consolidated_agno_docs.extend(agno_documents)
        
        if not custom_vector_db.exists():
            custom_vector_db.create()

        custom_vector_db.upsert(
            remove_duplicate_doc(consolidated_agno_docs),
            filters=kb_filters, 
            batch_size=1000
        )

    # elif req.type == "s3":
    #     if not (req.s3_bucket and req.s3_prefix):
    #         raise HTTPException(status_code=400, detail="`s3_bucket` and `s3_prefix` are required for s3")
    #     kb = S3KnowledgeBase(bucket=req.s3_bucket, prefix=req.s3_prefix, vector_db=vector_db)
    else:
        raise HTTPException(status_code=400, detail="Unsupported knowledge base type")
    
    return {"status": "success", "type": req.type, "name": req.name}



@router.get("/get")
def get_knowledgebases(
    user_id: str = Query(...), 
    db: Session = Depends(db_util.get_db),
    authorization: Optional[str] = Header(None)
):
    """
    Returns a list of knowledgebase tables for a given user (schema) using SQLAlchemy session.
    """

    validate_token(
        bearer_token=authorization,
        metadata=OKTAConfig.OKTA_JWT_OAUTH_CONFIG,
        okta_enable=OKTAConfig.OKTA_ENABLED,
        user_id=user_id
    )

    db_user = db_util.get_user_by_external_id(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        result = std_db_util.get_knowledgebases(user_id=user_id, db=db)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {e}")
    


@router.delete("/delete/{user_id}", status_code=200)
def delete_knowledgebase(
    user_id: str = Path(..., description="User ID as schema name"),
    kb_name: str = Query(..., description="knowledgebase as Table name to delete"),
    db: Session = Depends(db_util.get_db),
    authorization: Optional[str] = Header(None)
):
    
    validate_token(
        bearer_token=authorization,
        metadata=OKTAConfig.OKTA_JWT_OAUTH_CONFIG,
        okta_enable=OKTAConfig.OKTA_ENABLED,
        user_id=user_id
    )
    
    db_user = db_util.get_user_by_external_id(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        std_db_util.sync_kb_deletion(user_id=user_id, kb_name=kb_name, db=db)
        result = std_db_util.delete_knowledgebase(user_id=user_id, kb_name=kb_name, db=db)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {e}")
    