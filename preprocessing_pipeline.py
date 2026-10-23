import os
from files_processor import Files_Processor
from embedder import Embedder
from vector_store import VectorStore

class RAGPreprocessor:
    def __init__(self, docset_folder: str):
        self.docset_folder = docset_folder
        self.processor = Files_Processor()
        self.embedder = Embedder()
        self.vector_store = VectorStore(collection_name=os.path.basename(docset_folder))

    def process_and_store(self):
        files = [
            os.path.join(self.docset_folder, f)
            for f in os.listdir(self.docset_folder)
            if os.path.isfile(os.path.join(self.docset_folder, f))
        ]

        for file_path in files:
            document_id = os.path.basename(file_path)

            try:
                # Check if this document is already processed
                existing_chunks = self.vector_store.get_file_chunks(document_id)
                if existing_chunks:
                    print(f"Skipped '{document_id}' (already processed and stored).")
                    continue

                print(f"\nProcessing: {document_id}")
                chunks = self.processor.process_file(file_path)
                print(f" - Chunks generated: {len(chunks)}")

                enriched_chunks = self.embedder.generate_embeddings_and_enrich_chunks(chunks)
                print(f" - Embeddings generated.")

                self.vector_store.store_chunks(enriched_chunks)
                print(f" - Stored in Vector DB.\n")

            except Exception as e:
                print(f"Error processing {document_id}: {e}")

        self.vector_store.close()

    def add_new_file(self, file_name):
        file_path = os.path.join(self.docset_folder, file_name)
        if not os.path.isfile(file_path):
            print(f"File '{file_name}' does not exist in the folder.")
            return
        document_id = os.path.basename(file_path)
        try:
            # Check if this document is already processed
            existing_chunks = self.vector_store.get_file_chunks(document_id)
            if existing_chunks:
                print(f"Skipped '{document_id}' (already processed and stored).")
                return

            print(f"\nProcessing: {document_id}")
            chunks = self.processor.process_file(file_path)
            print(f" - Chunks generated: {len(chunks)}")

            enriched_chunks = self.embedder.generate_embeddings_and_enrich_chunks(chunks)
            print(f" - Embeddings generated.")

            self.vector_store.store_chunks(enriched_chunks)
            print(f" - Stored in Vector DB.\n")

        except Exception as e:
            print(f"Error processing {document_id}: {e}")

    def delete_file(self, file_name):
        """
        Delete a file's data (vector chunks) from the vector store.
        :param file_name: Name of the file to delete
        """
        self.vector_store.delete_by_filename(filename=file_name)

    def update_file(self, file_name):
        self.delete_file(file_name=file_name)
        self.add_new_file(file_name=file_name)

    def rename_file(self, src, dest):
        file_path = os.path.join(self.docset_folder, src)
        if not os.path.isfile(file_path):
            print(f"File '{src}' does not exist in the folder.")
            return
        old_doc_id = os.path.basename(file_path)

        file_path = os.path.join(self.docset_folder, dest)
        if not os.path.isfile(file_path):
            print(f"File '{dest}' does not exist in the folder.")
            return
        new_doc_id = os.path.basename(file_path)

        self.vector_store.update_document_id(old_doc_id, new_doc_id)

if __name__ == "__main__":
    folder = input("Enter the path to your docset folder: ").strip()

    if not os.path.exists(folder):
        print("Invalid folder path.")
    else:
        pipeline = RAGPreprocessor(docset_folder=folder)
        pipeline.process_and_store()
