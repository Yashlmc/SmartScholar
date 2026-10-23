from qdrant_client import QdrantClient, models
from qdrant_client.http.models import PointStruct
from typing import List, Dict
import uuid

class VectorStore:
    def __init__(self, collection_name: str, persist_dir: str = "./qdrant_vdb"):
        """
        Initialize Qdrant client and collection
        :param collection_name: Name of the collection
        :param persist_dir: Directory to store Qdrant data
        """
        self.client = QdrantClient(path=persist_dir)
        self.collection_name = collection_name
        self._initialize_collection()

    def _initialize_collection(self):
        """
        Create collection if it doesn't exist
        """
        if not self.collection_exists():
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=768,  # Fixed size for BGE embeddings
                    distance=models.Distance.COSINE
                )
            )

    def store_chunks(self, chunks: List[Dict]):
        """
        Store enriched chunks in Qdrant
        :param chunks: List of chunk dictionaries with embeddings
        """
        if not chunks:
            return

        # Generate UUIDs for each chunk
        points = [
            PointStruct(
                id=str(uuid.uuid4()),  # Generate UUID for each point
                vector=chunk["embedding"],
                payload={
                    "document_id": chunk["document_id"],
                    "chunk_order": chunk["chunk_order"],
                    "text": chunk["text"],
                    "token_count": chunk["token_count"],
                    "chunk_hash": chunk["chunk_hash"]
                }
            )
            for chunk in chunks
        ]

        # Upsert points into collection
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )

    def delete_by_filename(self, filename: str):
        """
        Delete all chunks associated with a specific file
        :param filename: Document ID to delete
        """
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="document_id",
                            match=models.MatchValue(value=filename))
                    ]
                )
            )
        )

    def get_file_chunks(self, filename: str) -> List[Dict]:
        """
        Retrieve all chunks for a specific file
        :param filename: Document ID to retrieve
        :return: List of chunk dictionaries
        """
        response = self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="document_id",
                        match=models.MatchValue(value=filename))
                ]
            ),
            limit=10000,  # Adjust based on expected max chunks per file
            with_payload=True,
            with_vectors=True
        )
        
        return [{
            "document_id": point.payload["document_id"],
            "chunk_order": point.payload["chunk_order"],
            "text": point.payload["text"],
            "token_count": point.payload["token_count"],
            "chunk_hash": point.payload["chunk_hash"],
            "score": 1
        } for point in response[0]]
    
    
    def update_document_id(self, old_document_id: str, new_document_id: str):
        """
        Update document_id for all stored chunks of a specific document.

        :param old_document_id: The current document filename.
        :param new_document_id: The new document filename.
        """
        # Retrieve all chunks for the old document ID
        chunks = self.get_file_chunks(old_document_id)
        if not chunks:
            print(f"No chunks found for {old_document_id}.")
            return

        # Modify document_id for all retrieved chunks
        updated_chunks = [
            {
                **chunk,
                "document_id": new_document_id
            }
            for chunk in chunks
        ]

        # Store updated chunks with the new document_id
        self.store_chunks(updated_chunks)

        # Delete the old document ID chunks
        self.delete_by_filename(old_document_id)
        print(f"Updated document_id from '{old_document_id}' to '{new_document_id}'.")

    def collection_exists(self) -> bool:
        """
        Check if collection exists in the database
        :return: True if collection exists, False otherwise
        """
        try:
            self.client.get_collection(self.collection_name)
            return True
        except Exception:
            return False
        
    def close(self):
        """
        Close the Qdrant client to release the file lock.
        """
        if self.client is not None:
            self.client = None  # Release reference
            print("Qdrant client closed.")

# # Example usage
# if __name__ == "__main__":
    # # Example enriched chunks
    # from sample_embd import se
    # enriched_chunks = [
    #     {
    #         "document_id": "sampletxt.txt",
    #         "chunk_order": 0,
    #         "text": "1.1 Overview of the Enterprise:",
    #         "token_count": 5,
    #         "chunk_hash": "fda52433ce6df2ced1541197d411fb52",
    #         "embedding": [-0.0128, 0.0219, -0.0089]  
    #     },
    #     {
    #         "document_id": "sampletxt.txt",
    #         "chunk_order": 1,
    #         "text": "YouTube, founded in 2005, has become the world's largest video-sharing platform...",
    #         "token_count": 70,
    #         "chunk_hash": "d59c057644df16c9d68e59e1d16a4e8a",
    #         "embedding": [0.0401, -0.0707, 0.0337] 
    #     }
    # ]

    # # Initialize the vector store
    # vector_store = VectorStore(collection_name="rag_chunks")

    # # # Store chunks
    # vector_store.store_chunks(se)

    # # # Retrieve stored chunks for a document
    # # retrieved_chunks = vector_store.get_file_chunks("sampletxt.txt")
    # # print("Retrieved Chunks:", retrieved_chunks)

    # # Delete all chunks for a document
    # # vector_store.delete_by_filename("sampletxt.txt")
    # # print("Embeddings deleted for sampletxt.txt")

    # vector_store.update_document_id("sampletxt.txt", "new.txt")

    # print("\nherer")
    # retrieved_chunks = vector_store.get_file_chunks("new.txt")
    # print("Retrieved Chunks:", retrieved_chunks)