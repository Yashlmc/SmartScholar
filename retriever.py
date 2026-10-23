# from typing import List, Dict, Optional
# from qdrant_client import QdrantClient, models
# from vector_store import VectorStore
# from embedder import Embedder

# class Retriever:
#     def __init__(self, vector_store: VectorStore, embedder: Embedder, score_threshold: float = 0.75):
#         """
#         Initialize retriever with dynamic result handling
#         :param score_threshold: Minimum similarity score (0-1)
#         """
#         self.vector_store = vector_store
#         self.embedder = embedder
#         self.score_threshold = score_threshold

#     def retrieve(self, query: str, score_threshold: Optional[float] = None) -> List[Dict]:
#         """
#         Retrieve chunks with optional dynamic threshold
#         """
#         threshold = score_threshold if score_threshold is not None else self.score_threshold
#         processed_query = self._prepare_query(query)
#         query_embedding = self.embedder.generate_embeddings([processed_query])[0]

#         results = self.vector_store.client.search(
#             collection_name=self.vector_store.collection_name,
#             query_vector=query_embedding.tolist(),
#             limit=1000,
#             score_threshold=threshold,
#             with_payload=True,
#             with_vectors=False
#         )

#         return self._format_results(results)
    
#     def hybrid_retrieve(self, query: str, alpha: float = 0.5, score_threshold: Optional[float] = None) -> List[Dict]:
#         """
#         Hybrid retrieval combining semantic and keyword search
#         :param query: User's search/question
#         :param alpha: Weight between semantic (alpha) and keyword (1-alpha)
#         :param score_threshold: Minimum similarity score (0-1)
#         :return: List of relevant chunks with scores
#         """
#         threshold = score_threshold if score_threshold is not None else self.score_threshold
#         processed_query = self._prepare_query(query)
#         query_embedding = self.embedder.generate_embeddings([processed_query])[0]

#         # Perform hybrid search
#         results = self.vector_store.client.search(
#             collection_name=self.vector_store.collection_name,
#             query_vector=query_embedding.tolist(),
#             query_filter=None,
#             search_params=models.SearchParams(
#                 hybrid=models.Hybrid(
#                     semantic=models.SemanticConfig(
#                         vectors=[query_embedding.tolist()],
#                         weight=alpha
#                     ),
#                     sparse=models.SparseConfig(
#                         indices=[],  # Implement BM25 here if needed
#                         values=[]
#                     )
#                 )
#             ),
#             limit=1000,
#             score_threshold=threshold,
#             with_payload=True,
#             with_vectors=False
#         )

#         return self._format_results(results)
    
#     def file_retrieval(self, filename: str):
#         return self.vector_store.get_file_chunks(filename)

#     def _prepare_query(self, query: str) -> str:
#         """Add BGE-specific instruction prefix"""
#         return f"Represent this sentence for searching relevant passages: {query}"

#     def _format_results(self, results) -> List[Dict]:
#         return [{
#             "document_id": result.payload["document_id"],
#             "chunk_order": result.payload["chunk_order"],
#             "text": result.payload["text"],
#             "token_count": result.payload["token_count"],
#             "chunk_hash": result.payload["chunk_hash"],
#             "score": result.score
#         } for result in results]


# if __name__ == "__main__":
#     vector_store = VectorStore(collection_name="rag_chunks")
#     embedder = Embedder()
    
#     retriever = Retriever(vector_store, embedder, 0.5)

#     result = retriever.retrieve("What is YouTube's history?")
#     print(result)

from typing import List, Dict, Optional
# from qdrant_client import QdrantClient, models
from vector_store import VectorStore
from embedder import Embedder

class Retriever:
    def __init__(self, vector_store: VectorStore, embedder: Embedder, score_threshold: float = 0.6):
        """
        Initialize retriever with dynamic result handling
        :param score_threshold: Minimum similarity score (0-1)
        """
        self.vector_store = vector_store
        self.embedder = embedder
        self.score_threshold = score_threshold

    def retrieve(self, query: str, score_threshold: Optional[float] = None) -> List[Dict]:
        """
        Retrieve chunks with optional dynamic threshold
        """
        threshold = score_threshold if score_threshold is not None else self.score_threshold
        processed_query = self._prepare_query(query)
        query_embedding = self.embedder.generate_embeddings([processed_query])[0]

        results = self.vector_store.client.query_points(
            collection_name=self.vector_store.collection_name,
            query=query_embedding.tolist(),
            limit=1000,
            score_threshold=threshold,
            with_payload=True,
            with_vectors=False
        )

        return self._format_results(results.points)
        # return results
    
    def file_retrieval(self, filename: str):
        return self.vector_store.get_file_chunks(filename)

    def _prepare_query(self, query: str) -> str:
        """Add BGE-specific instruction prefix"""
        return f"Represent this sentence for searching relevant passages: {query}"

    def _format_results(self, scored_points) -> List[Dict]:
        """
        Format Qdrant's ScoredPoint results into a list of dictionaries
        """
        formatted_results = []
        for point in scored_points:
            formatted_results.append({
                "document_id": point.payload["document_id"],
                "chunk_order": point.payload["chunk_order"],
                "text": point.payload["text"],
                "token_count": point.payload["token_count"],
                "chunk_hash": point.payload["chunk_hash"],
                "score": point.score
            })
        return formatted_results

# if __name__ == "__main__":
#     vector_store = VectorStore(collection_name="rag_chunks")
#     embedder = Embedder()
    
#     retriever = Retriever(vector_store, embedder, 0.4)

#     result = retriever.retrieve("What is YouTube's history?")
#     print(type(result))