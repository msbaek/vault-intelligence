#!/usr/bin/env python3
"""
FastAPI-based daemon server for Vault Intelligence System V2

Keeps BGE-M3 model and index in memory for fast search responses.
"""

import os
import sys
import logging
import signal
from pathlib import Path
from typing import Dict, List
from contextlib import asynccontextmanager

import yaml
import uvicorn
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from .features.advanced_search import AdvancedSearchEngine, SearchResult
from .core.vault_processor import Document

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_PORT = 8741
PID_FILE = Path.home() / ".vis-server.pid"

# Global state
_state: Dict = {
    "engine": None,
    "config": None,
    "indexed": False,
    "document_count": 0,
}


# Pydantic models
class SearchResultResponse(BaseModel):
    """Single search result"""
    path: str
    score: float
    title: str
    snippet: str
    rank: int = 0
    match_type: str = ""


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


def _convert_search_result(result: SearchResult, rank: int = 0) -> SearchResultResponse:
    """Convert SearchResult to SearchResultResponse"""
    # Extract document info
    doc: Document = result.document

    return SearchResultResponse(
        path=doc.path,
        score=result.similarity_score,
        title=doc.title,
        snippet=result.snippet or "",
        rank=rank,
        match_type=result.match_type
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown"""
    # Startup
    logger.info("Starting Vault Intelligence Server...")

    try:
        config = _get_config()
        _state["config"] = config

        logger.info("Initializing search engine...")
        engine = _init_engine()
        _state["engine"] = engine

        # load_index()는 AdvancedSearchEngine 생성자에서 이미 호출됨
        # 캐시로 복원 성공 시 build_index() 건너뜀
        if engine.indexed:
            logger.info("✅ Loaded existing index from cache")
            success = True
        else:
            logger.info("Building search index...")
            success = engine.build_index()

        if success:
            _state["indexed"] = True
            _state["document_count"] = len(engine.documents)
            logger.info(f"✅ Index built successfully: {_state['document_count']} documents")
        else:
            logger.warning("⚠️  Index build failed or no documents found")
            _state["indexed"] = False
            _state["document_count"] = 0

    except Exception as e:
        logger.error(f"Failed to initialize server: {e}")
        _state["indexed"] = False
        _state["document_count"] = 0

    yield

    # Shutdown
    logger.info("Shutting down Vault Intelligence Server...")
    _state["engine"] = None
    _state["config"] = None
    _state["indexed"] = False
    _state["document_count"] = 0


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
        return HealthResponse(
            status="ok" if _state["indexed"] else "not_indexed",
            indexed=_state["indexed"],
            document_count=_state["document_count"]
        )

    @app.get("/search", response_model=SearchResponse)
    async def search(
        query: str = Query(..., description="Search query"),
        top_k: int = Query(10, description="Number of results to return"),
        threshold: float = Query(0.0, description="Similarity threshold"),
        search_method: str = Query("hybrid", description="Search method: semantic, keyword, hybrid, colbert"),
        rerank: bool = Query(False, description="Enable reranking")
    ):
        """Search endpoint"""
        if not _state["indexed"]:
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
                _convert_search_result(r, rank=i+1)
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
                _state["indexed"] = True
                _state["document_count"] = len(engine.documents)

                return ReindexResponse(
                    document_count=_state["document_count"],
                    message=f"Successfully reindexed {_state['document_count']} documents"
                )
            else:
                raise HTTPException(status_code=500, detail="Reindex failed")

        except Exception as e:
            logger.error(f"Reindex failed: {e}")
            raise HTTPException(status_code=500, detail=f"Reindex failed: {str(e)}")

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
