#!/usr/bin/env python3
"""
FastAPI-based daemon server for Vault Intelligence System V2

Keeps BGE-M3 model and index in memory for fast search responses.
"""

import asyncio
import os
import sys
import logging
import signal
from pathlib import Path
from typing import Dict, List, Literal, Optional
from contextlib import asynccontextmanager

import yaml
import uvicorn
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from .features.advanced_search import AdvancedSearchEngine, SearchResult
from .core.vault_processor import Document
from .constants import DEFAULT_PORT, PID_FILE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global state - engine is the single source of truth for indexed/document_count
_state: Dict = {
    "engine": None,
    "config": None,
    "initializing": False,
}


def _is_indexed() -> bool:
    engine = _state["engine"]
    return engine is not None and engine.indexed


def _document_count() -> int:
    engine = _state["engine"]
    return len(engine.documents) if engine and hasattr(engine, 'documents') else 0


# Pydantic models
class SearchResultResponse(BaseModel):
    """Single search result. snippet/match_type은 include=index 모드에서 생략됨."""
    path: str
    score: float
    title: str
    rank: int = 0
    snippet: Optional[str] = None
    match_type: Optional[str] = None


class SearchResponse(BaseModel):
    """Search API response"""
    results: List[SearchResultResponse]
    query: str
    search_method: str
    total: int


class ReindexResponse(BaseModel):
    """Reindex API response"""
    document_count: int
    message: str


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    indexed: bool
    document_count: int


class DocumentResponse(BaseModel):
    """단일 문서 본문 응답."""
    path: str
    title: str
    content: str
    frontmatter: Dict
    tags: List[str] = []
    word_count: int = 0
    char_count: int = 0


class DocumentBatchRequest(BaseModel):
    """다중 문서 batch fetch 요청."""
    paths: List[str]


class DocumentBatchResponse(BaseModel):
    """다중 문서 batch fetch 응답."""
    documents: List[DocumentResponse]
    not_found: List[str] = []


def _get_config() -> Dict:
    """Load configuration from settings.yaml"""
    # Get data directory from environment or use default
    data_dir = os.environ.get('VIS_DATA_DIR', str(Path.home() / 'git/vault-intelligence'))
    config_path = Path(data_dir) / 'config' / 'settings.yaml'

    if not config_path.exists():
        logger.warning(f"Config file not found: {config_path}, using defaults")
        return {}

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        logger.info(f"Loaded config from {config_path}")
        return config
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return {}


def _init_engine() -> AdvancedSearchEngine:
    """Initialize AdvancedSearchEngine once"""
    config = _get_config()

    # Get vault path from environment or config
    vault_path = os.environ.get('VIS_VAULT_PATH')
    if not vault_path:
        vault_path = config.get('vault', {}).get('path', str(Path.home() / 'DocumentsLocal/msbaek_vault'))

    # Get cache directory
    data_dir = os.environ.get('VIS_DATA_DIR', str(Path.home() / 'git/vault-intelligence'))
    cache_dir = str(Path(data_dir) / 'cache')

    logger.info(f"Initializing search engine: vault={vault_path}, cache={cache_dir}")

    engine = AdvancedSearchEngine(
        vault_path=vault_path,
        cache_dir=cache_dir,
        config=config
    )

    return engine


def _convert_search_result(
    result: SearchResult,
    rank: int = 0,
    include: Literal["full", "index"] = "full",
) -> SearchResultResponse:
    """Convert SearchResult to SearchResultResponse. include='index' omits snippet/match_type."""
    doc: Document = result.document
    base = {
        "path": doc.path,
        "score": result.similarity_score,
        "title": doc.title or Path(doc.path).stem,
        "rank": rank,
    }
    if include == "index":
        return SearchResultResponse(**base)
    return SearchResultResponse(
        **base,
        snippet=result.snippet or "",
        match_type=result.match_type or "",
    )


async def _build_index_background():
    """Build index in background thread so health endpoint responds immediately"""
    _state["initializing"] = True
    try:
        engine = await asyncio.get_event_loop().run_in_executor(None, _init_engine)
        _state["engine"] = engine

        if engine.indexed:
            logger.info("✅ Loaded existing index from cache")
        else:
            logger.info("Building search index...")
            success = await asyncio.get_event_loop().run_in_executor(None, engine.build_index)
            if not success:
                logger.warning("⚠️  Index build failed or no documents found")

        logger.info(f"✅ Index ready: {_document_count()} documents")
    except Exception as e:
        logger.error(f"Failed to initialize engine: {e}")
    finally:
        _state["initializing"] = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown"""
    logger.info("Starting Vault Intelligence Server...")

    config = _get_config()
    _state["config"] = config

    # Start index building in background — health endpoint available immediately
    task = asyncio.create_task(_build_index_background())

    yield

    # Shutdown
    task.cancel()
    logger.info("Shutting down Vault Intelligence Server...")
    _state["engine"] = None
    _state["config"] = None


def create_app() -> FastAPI:
    """Create FastAPI application (factory function for testability)"""
    app = FastAPI(
        title="Vault Intelligence Server",
        description="BGE-M3 based semantic search server for Obsidian vaults",
        version="2.0.0",
        lifespan=lifespan
    )

    @app.get("/health", response_model=HealthResponse)
    async def health_check():
        """Health check endpoint"""
        if _state["initializing"]:
            status = "initializing"
        elif _is_indexed():
            status = "ok"
        else:
            status = "not_indexed"

        return HealthResponse(
            status=status,
            indexed=_is_indexed(),
            document_count=_document_count()
        )

    @app.get("/search", response_model=SearchResponse, response_model_exclude_none=True)
    async def search(
        query: str = Query(..., description="Search query"),
        top_k: int = Query(10, description="Number of results to return"),
        threshold: float = Query(0.0, description="Similarity threshold"),
        search_method: str = Query("hybrid", description="Search method: semantic, keyword, hybrid, colbert"),
        rerank: bool = Query(False, description="Enable reranking"),
        include: Literal["full", "index"] = Query(
            "full",
            description="Response depth: 'full'(snippet 포함) or 'index'(path/score/title/rank만)",
        ),
    ):
        """Search endpoint"""
        if not _is_indexed():
            raise HTTPException(status_code=503, detail="Index not built yet")

        engine: AdvancedSearchEngine = _state["engine"]
        if engine is None:
            raise HTTPException(status_code=503, detail="Search engine not initialized")

        try:
            # Execute search based on method and rerank option
            if rerank:
                results: List[SearchResult] = engine.search_with_reranking(
                    query=query,
                    search_method=search_method,
                    initial_k=min(top_k * 3, 100),
                    final_k=top_k,
                    threshold=threshold,
                    use_reranker=True
                )
            else:
                # Direct search without reranking
                if search_method == "semantic":
                    results = engine.semantic_search(query, top_k=top_k, threshold=threshold)
                elif search_method == "keyword":
                    results = engine.keyword_search(query, top_k=top_k)
                elif search_method == "colbert":
                    results = engine.colbert_search(query, top_k=top_k, threshold=threshold)
                elif search_method == "hybrid":
                    results = engine.hybrid_search(query, top_k=top_k, threshold=threshold)
                else:
                    raise HTTPException(status_code=400, detail=f"Invalid search method: {search_method}")

            # Convert results
            response_results = [
                _convert_search_result(r, rank=i+1, include=include)
                for i, r in enumerate(results)
            ]

            return SearchResponse(
                results=response_results,
                query=query,
                search_method=search_method,
                total=len(response_results)
            )

        except HTTPException:
            # Re-raise HTTP exceptions as-is
            raise
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

    @app.post("/reindex", response_model=ReindexResponse)
    async def reindex(force: bool = Query(False, description="Force rebuild index")):
        """Reindex endpoint"""
        engine: AdvancedSearchEngine = _state["engine"]
        if engine is None:
            raise HTTPException(status_code=503, detail="Search engine not initialized")

        try:
            logger.info(f"Reindexing... (force={force})")
            success = engine.build_index(force_rebuild=force)

            if success:
                return ReindexResponse(
                    document_count=_document_count(),
                    message=f"Successfully reindexed {_document_count()} documents"
                )
            else:
                raise HTTPException(status_code=500, detail="Reindex failed")

        except Exception as e:
            logger.error(f"Reindex failed: {e}")
            raise HTTPException(status_code=500, detail=f"Reindex failed: {str(e)}")

    @app.get("/document", response_model=DocumentResponse)
    async def get_document(path: str = Query(..., description="Document path (vault-relative)")):
        """단일 문서 본문/frontmatter 반환."""
        if not _is_indexed():
            raise HTTPException(status_code=503, detail="Index not built yet")
        engine: AdvancedSearchEngine = _state["engine"]
        if engine is None:
            raise HTTPException(status_code=503, detail="Search engine not initialized")

        doc = next((d for d in engine.documents if d.path == path), None)
        if doc is None:
            raise HTTPException(status_code=404, detail=f"Document not found: {path}")

        return DocumentResponse(
            path=doc.path,
            title=doc.title or "",
            content=doc.content or "",
            frontmatter=doc.frontmatter or {},
            tags=list(doc.tags or []),
            word_count=getattr(doc, "word_count", 0),
            char_count=getattr(doc, "char_count", 0),
        )

    @app.post("/document/batch", response_model=DocumentBatchResponse)
    async def get_document_batch(request: DocumentBatchRequest):
        """다중 문서 batch fetch — not found는 not_found 배열로 반환."""
        if not _is_indexed():
            raise HTTPException(status_code=503, detail="Index not built yet")
        engine: AdvancedSearchEngine = _state["engine"]
        if engine is None:
            raise HTTPException(status_code=503, detail="Search engine not initialized")

        by_path = {d.path: d for d in engine.documents}
        documents: List[DocumentResponse] = []
        not_found: List[str] = []

        for p in request.paths:
            doc = by_path.get(p)
            if doc is None:
                not_found.append(p)
                continue
            documents.append(DocumentResponse(
                path=doc.path,
                title=doc.title or "",
                content=doc.content or "",
                frontmatter=doc.frontmatter or {},
                tags=list(doc.tags or []),
                word_count=getattr(doc, "word_count", 0),
                char_count=getattr(doc, "char_count", 0),
            ))

        return DocumentBatchResponse(documents=documents, not_found=not_found)

    return app


def _write_pid_file(pid: int):
    """Write PID to file"""
    try:
        PID_FILE.write_text(str(pid))
        logger.info(f"PID file written: {PID_FILE}")
    except Exception as e:
        logger.error(f"Failed to write PID file: {e}")


def _remove_pid_file():
    """Remove PID file"""
    try:
        if PID_FILE.exists():
            PID_FILE.unlink()
            logger.info(f"PID file removed: {PID_FILE}")
    except Exception as e:
        logger.error(f"Failed to remove PID file: {e}")


def _handle_shutdown(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, shutting down...")
    _remove_pid_file()
    sys.exit(0)


def run_server(host: str = "127.0.0.1", port: int = DEFAULT_PORT):
    """Run the server with uvicorn

    Args:
        host: Host to bind to
        port: Port to bind to
    """
    # Set up signal handlers
    signal.signal(signal.SIGINT, _handle_shutdown)
    signal.signal(signal.SIGTERM, _handle_shutdown)

    # Write PID file
    _write_pid_file(os.getpid())

    try:
        # Create app and run
        app = create_app()
        uvicorn.run(app, host=host, port=port, log_level="info")
    finally:
        _remove_pid_file()


if __name__ == "__main__":
    run_server()
