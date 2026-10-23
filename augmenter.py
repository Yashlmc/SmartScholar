import os
from typing import List, Dict, Optional
from sentence_transformers import CrossEncoder

class Augmenter:
    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        local_dir: str = "local/cross-encoder",
        max_tokens: int = 4096
    ):
        """
        Initialize augmenter with re-ranker and token management
        :param model_name: HF model name for cross-encoder
        :param local_dir: Local directory to store model
        :param max_tokens: Context window size limit
        """
        self.model_name = model_name
        self.local_dir = local_dir
        self.max_tokens = max_tokens
        
        if not os.path.exists(local_dir):
            self.download_model(self.model_name)
            
        self.reranker = CrossEncoder(self.local_dir)

    @classmethod
    def download_model(cls, model_name: str, target_dir: str = "local/cross-encoder"):
        """
        Download and save cross-encoder model
        :param model_name: HF model identifier
        :param target_dir: Directory to save model files
        """
        os.makedirs(target_dir, exist_ok=True)
        
        try:
            # print(f"Downloading {model_name}...")
            model = CrossEncoder(model_name)
            model.save(target_dir)
            # print(f"Model saved to {target_dir}")
        except Exception as e:
            raise RuntimeError(f"Model download failed: {str(e)}") from e

    def augment(self, query: str, retrieved_chunks: List[Dict], max_tokens: Optional[int] = None) -> Dict:
        """
        Enhanced augmentation with re-ranking and token management
        :return: {
            "query": original query,
            "context": processed context,
            "sources": list of source metadata,
            "token_count": total tokens
        }
        """
        max_tokens = max_tokens if max_tokens is not None else self.max_tokens
        if not retrieved_chunks:
            return {
                "query": query,
                "context": "",
                "sources": [],
                "token_count": 0
            }

        # Re-rank chunks using cross-encoder
        rerank_inputs = [(query, chunk["text"]) for chunk in retrieved_chunks]
        scores = self.reranker.predict(rerank_inputs)
        
        # Update chunks with re-rank scores
        for chunk, score in zip(retrieved_chunks, scores):
            chunk["rerank_score"] = float(score)  # Convert numpy float to native float

        # Sort by combined scores (rerank_score * original_score)
        sorted_chunks = sorted(
            retrieved_chunks,
            key=lambda x: x["rerank_score"] * x["score"],
            reverse=True
        )

        # Build context within token limit
        context = []
        sources = []
        token_count = 0
        
        for chunk in sorted_chunks:
            chunk_tokens = chunk["token_count"]
            
            if token_count + chunk_tokens > self.max_tokens:
                break
                
            context.append(chunk["text"])
            token_count += chunk_tokens
            sources.append({
                "document_id": chunk["document_id"],
                "chunk_order": chunk["chunk_order"],
                "original_score": chunk["score"],
                "rerank_score": chunk["rerank_score"]
            })

        return {
            "query": query,
            "context": "\n\n".join(context),
            "sources": sources,
            "token_count": token_count
        }


# if __name__ == "__main__":
    
#     retrieved_chunks = [{'document_id': 'new.txt', 'chunk_order': 1, 'text': "YouTube, founded in 2005, has become the world's largest video-sharing platform...", 'token_count': 70, 'chunk_hash': 'd59c057644df16c9d68e59e1d16a4e8a', 'score': 0.6280466158966196}, {'document_id': 'new.txt', 'chunk_order': 0, 'text': '1.1 Overview of the Enterprise:', 'token_count': 5, 'chunk_hash': 'fda52433ce6df2ced1541197d411fb52', 'score': 0.42788867665772556}]

#     # First-time usage (auto-downloads model)
#     augmenter = Augmenter()

#     # Process retrieved chunks
#     augmented = augmenter.augment("YouTube history", retrieved_chunks, max_tokens=5000)

#     # print(f"Context ({augmented['token_count']} tokens):")
#     # print(augmented["context"])

#     # print("\nSources:")
#     # for source in augmented["sources"]:
#     #     print(f"- {source['document_id']} (Chunk {source['chunk_order']})")
#     #     print(f"  Original: {source['original_score']:.3f}, Rerank: {source['rerank_score']:.3f}")

#     print(augmented)