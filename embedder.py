import os
from typing import List
from sentence_transformers import SentenceTransformer
import numpy as np

class Embedder:
    def __init__(self):
        """
        Initialize with locally stored BGE model
        :param model_path: Path to downloaded model within 'local' directory
        """
        self.model_path = "local/bge-base-en-v1.5" 
        self.model = None
        self.embedding_dim = 768  # For bge-base model
        self._load_model()

    def _load_model(self):
        """Load model from local directory with validation"""
        if not os.path.exists(self.model_path):
            Embedder.download_model()

        self.model = SentenceTransformer(self.model_path, device="cpu")
        self.embedding_dim = self.model.get_sentence_embedding_dimension()

    @classmethod
    def download_model(cls, save_dir: str = "local"):
        """One-time model download (requires internet connection)"""
        os.makedirs(save_dir, exist_ok=True)
        model = SentenceTransformer("BAAI/bge-base-en-v1.5")
        model.save(os.path.join(save_dir, "bge-base-en-v1.5"))
        print(f"Model downloaded and saved to {save_dir}/bge-base-en-v1.5")

    def _add_instruction_prefix(self, texts: List[str]) -> List[str]:
        """Add BGE-specific instruction prefix"""
        prompt = "Represent this sentence for searching relevant passages: "
        return [f"{prompt} {text}" for text in texts]

    def generate_embeddings(self, chunks: List[str], normalize: bool = True) -> np.ndarray:
        """
        Generate embeddings for text chunks
        :param chunks: List of text strings to embed
        :return: Numpy array of shape (num_chunks, 768)
        """
        instruction_texts = self._add_instruction_prefix(chunks)
        return self.model.encode(
            instruction_texts,
            batch_size=32,
            convert_to_numpy=True,
            normalize_embeddings=normalize,
            show_progress_bar=False,
            device="cpu"
        )
    
    def generate_embeddings_and_enrich_chunks(self, chunks: List[dict], normalize: bool = True) -> List[dict]:
        """
        Generate embeddings for text chunks and attach metadata
        :param chunks: List of chunk dictionaries
        :return: List of dictionaries with embeddings and metadata
        """
        # Extract text from chunks
        texts = [chunk["text"] for chunk in chunks]
        
        # Generate embeddings
        instruction_texts = self._add_instruction_prefix(texts)
        embeddings = self.model.encode(
            instruction_texts,
            batch_size=32,
            convert_to_numpy=True,
            normalize_embeddings=normalize,
            show_progress_bar=False,
            device="cpu"
        )

        # Attach embeddings to chunks
        enriched_chunks = []
        for chunk, embedding in zip(chunks, embeddings):
            enriched_chunk = {
                **chunk,  # Preserve all original metadata
                "embedding": embedding.tolist(),  # Add embedding
            }
            enriched_chunks.append(enriched_chunk)

        return enriched_chunks

    @property
    def model_info(self) -> dict:
        """Get model metadata"""
        return {
            "model_name": self.model_path,
            "embedding_dim": self.embedding_dim,
            "max_seq_length": self.model.get_max_seq_length(),
            "location": self.model_path
        }

if __name__ == "__main__":
    from pprint import pprint
    embedder = Embedder()

    # Sample chunks from document processing
    # chunks = [
    #     "Large language models have revolutionized NLP.",
    #     "Vector databases enable efficient similarity search.",
    #     "BGE embeddings provide state-of-the-art retrieval."
    # ]

    chunks = [
    {
        "document_id": "sampletxt.txt",
        "chunk_order": 0,
        "text": "1.1 Overview of the Enterprise:",
        "token_count": 5,
        "chunk_hash": "fda52433ce6df2ced1541197d411fb52"
    },
    {
        "document_id": "sampletxt.txt",
        "chunk_order": 1,
        "text": "YouTube, founded in 2005, has become the world's largest video-sharing platform...",
        "token_count": 70,
        "chunk_hash": "d59c057644df16c9d68e59e1d16a4e8a"
    }
    ]

    # Generate embeddings
    embeddings = embedder.generate_embeddings_and_enrich_chunks(chunks)

    print(len(embeddings))

    # print(f"Embeddings shape: {embeddings.shape}")  # (3, 768)
    print(f"Sample embedding: {embeddings}")  
    # print(f"Sample embedding: {embeddings[0][:10]}")  # First 10 dimensions

    # Access model info
    print(embedder.model_info)