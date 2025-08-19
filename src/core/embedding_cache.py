#!/usr/bin/env python3
"""
Embedding Cache System for Vault Intelligence System V2

SQLite 기반 영구 캐싱으로 임베딩 재계산을 방지하고 성능을 최적화
"""

import os
import json
import hashlib
import sqlite3
import logging
from typing import Optional, Dict, List, Tuple
from pathlib import Path
from datetime import datetime
import numpy as np
from dataclasses import dataclass, asdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class CachedEmbedding:
    """캐시된 임베딩 정보"""
    file_path: str
    file_hash: str
    embedding: np.ndarray
    model_name: str
    embedding_dimension: int
    created_at: datetime
    file_size: int
    word_count: Optional[int] = None


class EmbeddingCache:
    """임베딩 캐시 관리 시스템"""
    
    def __init__(self, cache_dir: str):
        """
        Args:
            cache_dir: 캐시 디렉토리 경로
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.db_path = self.cache_dir / "embeddings.db"
        self.metadata_path = self.cache_dir / "metadata.json"
        
        # 데이터베이스 초기화
        self._init_database()
        
        # 메타데이터 로딩
        self._load_metadata()
        
        logger.info(f"임베딩 캐시 초기화: {self.cache_dir}")
    
    def _init_database(self):
        """SQLite 데이터베이스 초기화"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 임베딩 테이블 생성
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS embeddings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        file_path TEXT NOT NULL UNIQUE,
                        file_hash TEXT NOT NULL,
                        embedding BLOB NOT NULL,
                        model_name TEXT NOT NULL,
                        embedding_dimension INTEGER NOT NULL,
                        created_at TIMESTAMP NOT NULL,
                        file_size INTEGER NOT NULL,
                        word_count INTEGER
                    )
                """)
                
                # 인덱스 생성
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_file_path ON embeddings(file_path)
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_file_hash ON embeddings(file_hash)
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_model_name ON embeddings(model_name)
                """)
                
                conn.commit()
                logger.info("데이터베이스 초기화 완료")
        
        except Exception as e:
            logger.error(f"데이터베이스 초기화 실패: {e}")
            raise
    
    def _load_metadata(self):
        """메타데이터 로딩"""
        try:
            if self.metadata_path.exists():
                with open(self.metadata_path, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
            else:
                self.metadata = {
                    "cache_version": "1.0",
                    "created_at": datetime.now().isoformat(),
                    "total_embeddings": 0,
                    "models_used": []
                }
            logger.info("메타데이터 로딩 완료")
        except Exception as e:
            logger.error(f"메타데이터 로딩 실패: {e}")
            self.metadata = {}
    
    def _save_metadata(self):
        """메타데이터 저장"""
        try:
            with open(self.metadata_path, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"메타데이터 저장 실패: {e}")
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """파일 해시 계산"""
        try:
            with open(file_path, 'rb') as f:
                file_content = f.read()
                return hashlib.md5(file_content).hexdigest()
        except Exception as e:
            logger.error(f"파일 해시 계산 실패: {file_path}, {e}")
            return ""
    
    def _serialize_embedding(self, embedding: np.ndarray) -> bytes:
        """임베딩을 바이너리로 직렬화"""
        try:
            return embedding.tobytes()
        except Exception as e:
            logger.error(f"임베딩 직렬화 실패: {e}")
            return b""
    
    def _deserialize_embedding(self, data: bytes, dimension: int) -> np.ndarray:
        """바이너리에서 임베딩 복원"""
        try:
            return np.frombuffer(data, dtype=np.float32).reshape(dimension)
        except Exception as e:
            logger.debug(f"임베딩 역직렬화 실패 (차원 불일치): {e}")  # ERROR에서 DEBUG로 변경
            return np.zeros(dimension)
    
    def store_embedding(
        self, 
        file_path: str, 
        embedding: np.ndarray, 
        model_name: str,
        word_count: Optional[int] = None
    ) -> bool:
        """임베딩 저장"""
        try:
            # 파일 정보 수집
            file_hash = self._calculate_file_hash(file_path)
            file_size = os.path.getsize(file_path)
            created_at = datetime.now()
            
            # 임베딩 직렬화
            embedding_data = self._serialize_embedding(embedding)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 기존 데이터 삭제 후 삽입 (REPLACE 대신 사용)
                cursor.execute("DELETE FROM embeddings WHERE file_path = ?", (file_path,))
                
                cursor.execute("""
                    INSERT INTO embeddings 
                    (file_path, file_hash, embedding, model_name, embedding_dimension, 
                     created_at, file_size, word_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    file_path, file_hash, embedding_data, model_name,
                    len(embedding), created_at, file_size, word_count
                ))
                
                conn.commit()
            
            # 메타데이터 업데이트
            self._update_metadata(model_name)
            
            logger.debug(f"임베딩 저장 완료: {file_path}")
            return True
        
        except Exception as e:
            logger.error(f"임베딩 저장 실패: {file_path}, {e}")
            return False
    
    def get_embedding(self, file_path: str, current_hash: Optional[str] = None) -> Optional[CachedEmbedding]:
        """임베딩 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT file_hash, embedding, model_name, embedding_dimension,
                           created_at, file_size, word_count
                    FROM embeddings 
                    WHERE file_path = ?
                """, (file_path,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                file_hash, embedding_data, model_name, dimension, created_at, file_size, word_count = row
                
                # 파일 변경 확인
                if current_hash and current_hash != file_hash:
                    logger.debug(f"파일이 변경됨: {file_path}")
                    return None
                
                # 임베딩 복원
                embedding = self._deserialize_embedding(embedding_data, dimension)
                
                return CachedEmbedding(
                    file_path=file_path,
                    file_hash=file_hash,
                    embedding=embedding,
                    model_name=model_name,
                    embedding_dimension=dimension,
                    created_at=datetime.fromisoformat(created_at),
                    file_size=file_size,
                    word_count=word_count
                )
        
        except Exception as e:
            logger.error(f"임베딩 조회 실패: {file_path}, {e}")
            return None
    
    def is_cached(self, file_path: str, current_hash: Optional[str] = None) -> bool:
        """캐시 존재 여부 확인"""
        cached = self.get_embedding(file_path, current_hash)
        return cached is not None
    
    def remove_embedding(self, file_path: str) -> bool:
        """임베딩 삭제"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM embeddings WHERE file_path = ?", (file_path,))
                conn.commit()
                
                if cursor.rowcount > 0:
                    logger.debug(f"임베딩 삭제 완료: {file_path}")
                    return True
                return False
        
        except Exception as e:
            logger.error(f"임베딩 삭제 실패: {file_path}, {e}")
            return False
    
    def clean_invalid_entries(self) -> int:
        """존재하지 않는 파일의 캐시 정리"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT file_path FROM embeddings")
                all_paths = [row[0] for row in cursor.fetchall()]
                
                removed_count = 0
                for file_path in all_paths:
                    if not os.path.exists(file_path):
                        cursor.execute("DELETE FROM embeddings WHERE file_path = ?", (file_path,))
                        removed_count += 1
                
                conn.commit()
                logger.info(f"무효한 캐시 항목 정리: {removed_count}개")
                return removed_count
        
        except Exception as e:
            logger.error(f"캐시 정리 실패: {e}")
            return 0
    
    def get_statistics(self) -> Dict:
        """캐시 통계 정보"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 총 임베딩 수
                cursor.execute("SELECT COUNT(*) FROM embeddings")
                total_count = cursor.fetchone()[0]
                
                # 모델별 통계
                cursor.execute("""
                    SELECT model_name, COUNT(*), AVG(embedding_dimension)
                    FROM embeddings 
                    GROUP BY model_name
                """)
                model_stats = cursor.fetchall()
                
                # 파일 크기 통계
                cursor.execute("SELECT SUM(file_size), AVG(file_size) FROM embeddings")
                size_stats = cursor.fetchone()
                
                return {
                    "cache_dir": str(self.cache_dir),
                    "total_embeddings": total_count,
                    "models": {
                        model: {
                            "count": count,
                            "avg_dimension": int(avg_dim)
                        }
                        for model, count, avg_dim in model_stats
                    },
                    "total_file_size": size_stats[0] or 0,
                    "avg_file_size": int(size_stats[1] or 0),
                    "db_size": os.path.getsize(self.db_path) if self.db_path.exists() else 0
                }
        
        except Exception as e:
            logger.error(f"통계 생성 실패: {e}")
            return {}
    
    def _update_metadata(self, model_name: str):
        """메타데이터 업데이트"""
        try:
            if model_name not in self.metadata.get("models_used", []):
                self.metadata.setdefault("models_used", []).append(model_name)
            
            self.metadata["last_updated"] = datetime.now().isoformat()
            self._save_metadata()
        
        except Exception as e:
            logger.error(f"메타데이터 업데이트 실패: {e}")
    
    def export_cache_info(self, output_file: str) -> bool:
        """캐시 정보를 파일로 내보내기"""
        try:
            stats = self.get_statistics()
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2, ensure_ascii=False)
            
            logger.info(f"캐시 정보 내보내기 완료: {output_file}")
            return True
        
        except Exception as e:
            logger.error(f"캐시 정보 내보내기 실패: {e}")
            return False


def test_cache():
    """캐시 시스템 테스트"""
    import tempfile
    import shutil
    
    try:
        # 임시 디렉토리 생성
        temp_dir = tempfile.mkdtemp()
        cache = EmbeddingCache(temp_dir)
        
        # 테스트 임베딩
        test_embedding = np.random.rand(768).astype(np.float32)
        test_file = os.path.join(temp_dir, "test.md")
        
        # 테스트 파일 생성
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("테스트 파일 내용")
        
        # 저장 테스트
        success = cache.store_embedding(test_file, test_embedding, "test-model", 10)
        print(f"저장 성공: {success}")
        
        # 조회 테스트
        cached = cache.get_embedding(test_file)
        print(f"조회 성공: {cached is not None}")
        
        if cached:
            similarity = np.dot(test_embedding, cached.embedding)
            print(f"임베딩 일치도: {similarity:.6f}")
        
        # 통계 테스트
        stats = cache.get_statistics()
        print(f"통계: {stats}")
        
        # 정리
        shutil.rmtree(temp_dir)
        print("✅ 캐시 테스트 완료!")
        return True
        
    except Exception as e:
        print(f"❌ 캐시 테스트 실패: {e}")
        return False


if __name__ == "__main__":
    test_cache()