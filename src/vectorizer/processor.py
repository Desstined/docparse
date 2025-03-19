from typing import List, Dict, Union, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
import torch
from functools import lru_cache
import logging

from src.config import settings

logger = logging.getLogger(__name__)

class Vectorizer:
    def __init__(self):
        """Initialize the vectorizer with the specified model."""
        self.model_name = settings.EMBEDDING_MODEL
        self.vector_dimension = settings.VECTOR_DIMENSION
        self.batch_size = settings.BATCH_SIZE
        
        # Initialize the model
        try:
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"Successfully loaded model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to load model {self.model_name}: {str(e)}")
            raise

    @lru_cache(maxsize=1000)
    def get_embedding(self, text: str) -> np.ndarray:
        """Get embedding for a single text string with caching."""
        try:
            embedding = self.model.encode(
                text,
                convert_to_numpy=True,
                normalize_embeddings=True
            )
            return embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise

    def get_embeddings_batch(self, texts: List[str]) -> np.ndarray:
        """Get embeddings for a batch of texts."""
        try:
            embeddings = self.model.encode(
                texts,
                batch_size=self.batch_size,
                convert_to_numpy=True,
                normalize_embeddings=True
            )
            return embeddings
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {str(e)}")
            raise

    def get_embeddings_with_metadata(
        self,
        texts: List[str],
        metadata: Optional[List[Dict]] = None
    ) -> List[Dict]:
        """Get embeddings with associated metadata."""
        try:
            embeddings = self.get_embeddings_batch(texts)
            
            results = []
            for i, (text, embedding) in enumerate(zip(texts, embeddings)):
                result = {
                    'text': text,
                    'embedding': embedding,
                    'dimension': self.vector_dimension
                }
                
                if metadata and i < len(metadata):
                    result.update(metadata[i])
                
                results.append(result)
            
            return results
        except Exception as e:
            logger.error(f"Error generating embeddings with metadata: {str(e)}")
            raise

    def compute_similarity(
        self,
        embedding1: np.ndarray,
        embedding2: np.ndarray
    ) -> float:
        """Compute cosine similarity between two embeddings."""
        try:
            similarity = np.dot(embedding1, embedding2) / (
                np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
            )
            return float(similarity)
        except Exception as e:
            logger.error(f"Error computing similarity: {str(e)}")
            raise

    def find_similar_texts(
        self,
        query_text: str,
        texts: List[str],
        top_k: int = 5
    ) -> List[Dict[str, Union[str, float]]]:
        """Find similar texts using cosine similarity."""
        try:
            # Get query embedding
            query_embedding = self.get_embedding(query_text)
            
            # Get embeddings for all texts
            text_embeddings = self.get_embeddings_batch(texts)
            
            # Compute similarities
            similarities = [
                self.compute_similarity(query_embedding, text_embedding)
                for text_embedding in text_embeddings
            ]
            
            # Get top k results
            top_indices = np.argsort(similarities)[-top_k:][::-1]
            
            results = []
            for idx in top_indices:
                results.append({
                    'text': texts[idx],
                    'similarity': similarities[idx]
                })
            
            return results
        except Exception as e:
            logger.error(f"Error finding similar texts: {str(e)}")
            raise

    def get_model_info(self) -> Dict[str, Union[str, int]]:
        """Get information about the current model."""
        return {
            'model_name': self.model_name,
            'vector_dimension': self.vector_dimension,
            'batch_size': self.batch_size,
            'device': str(self.model.device)
        }

    def clear_cache(self):
        """Clear the embedding cache."""
        self.get_embedding.cache_clear() 