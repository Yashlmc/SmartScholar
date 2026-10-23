import hashlib
import json
from langchain.text_splitter import RecursiveCharacterTextSplitter

class Chunker:
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    def _generate_metadata(self, chunk: str, document_id: str, chunk_order: int) -> dict:
        token_count = len(chunk.split())  # Token count (word count)
        chunk_hash = hashlib.md5(chunk.encode()).hexdigest()  # Chunk hash

        return {
            "document_id": document_id,
            "chunk_order": chunk_order,
            "text": chunk,
            "token_count": token_count,
            "chunk_hash": chunk_hash
        }

    def chunk_text(self, text: str, document_id: str):
        chunks = self.text_splitter.split_text(text)
        chunked_data = [
            self._generate_metadata(chunk, document_id, i) for i, chunk in enumerate(chunks)
        ]
        return chunked_data

    def save_to_json(self, chunked_data, filename="chunked_output.json"):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(chunked_data, f, indent=4, ensure_ascii=False)

# Example usage
# if __name__ == "__main__":
#     with open("sampletxt.txt", 'r', encoding="utf-8") as file:
#         text = file.read()

#     chunker = Chunker(chunk_size=500, chunk_overlap=50)
#     document_id = "sampletxt.txt"

#     chunks_with_metadata = chunker.chunk_text(text, document_id)

#     # Print chunks
#     for chunk in chunks_with_metadata:
#         print(chunk, "\n", "-" * 40)

#     # Save to JSON
#     chunker.save_to_json(chunks_with_metadata)
