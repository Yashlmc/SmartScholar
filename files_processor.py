import os
import fitz
import docx
from chunker import Chunker

class Files_Processor:
    def __init__(self):
        self.chunker = Chunker()

    def _extract_text_from_txt(self, file_path: str) -> str:
        """Extracts text from a TXT file."""
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    def _extract_text_from_docx(self, file_path: str) -> str:
        """Extracts text from a DOCX file."""
        doc = docx.Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])

    def _extract_text_from_pdf(self, file_path: str) -> str:
        """Extracts text from a PDF file."""
        text = []
        with fitz.open(file_path) as pdf:
            for page in pdf:
                text.append(page.get_text("text"))
        return "\n".join(text)

    def _select_chunker(self, file_extension: str):
        """Selects the appropriate chunker based on file type."""
        if file_extension == ".py":
            return None     # PythonChunker(self.chunk_size, self.chunk_overlap)
        else:
            return self.chunker  # Default chunker

    def process_file(self, file_path: str):
        """Extracts text from file, selects the appropriate chunker, and returns chunks."""
        ext = os.path.splitext(file_path)[-1].lower()

        extract_methods = {
            ".txt": self._extract_text_from_txt,
            ".docx": self._extract_text_from_docx,
            ".pdf": self._extract_text_from_pdf
        }

        if ext not in extract_methods:
            raise ValueError(f"Unsupported file type: {ext}")

        text = extract_methods[ext](file_path)
        document_id = os.path.basename(file_path)  # Use filename as document ID

        chunker = self._select_chunker(ext)
        return chunker.chunk_text(text, document_id)
    

# # # Example usage
# if __name__ == "__main__":
#     processor = Files_Processor()
    
#     # file_path = "docset/Life is Short And So Is This Book.pdf"
#     # file_path = "docset/SOFTWARE TESTING.docx"
#     file_path = "docset/sampletxt.txt"
#     chunks = processor.process_file(file_path)

#     print(chunks)
#     print("\n\n\n")

#     for chunk in chunks:
#         print(chunk, "\n", "-" * 40)
