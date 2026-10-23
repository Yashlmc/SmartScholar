import os
from files_processor import Files_Processor
from embedder import Embedder
from vector_store import VectorStore
from retriever import Retriever
from augmenter import Augmenter
from generator3 import Generator

from query_analyzer import FileNameExtractor, QueryClassifier

class RAGPipeline:
    def __init__(self, docset_folder: str):
        self.docset_folder = docset_folder
        self.collection_name = os.path.basename(docset_folder)
        self.processor = Files_Processor()
        self.embedder = Embedder()
        self.vector_store = VectorStore(collection_name=self.collection_name)
        self.retriever = Retriever(self.vector_store, self.embedder)
        self.augmenter = Augmenter()
        self.generator = Generator()
        self.query_classifier : QueryClassifier = QueryClassifier(model_path="query_processing/local/query_classifier_model.pkl", bert_model="bert-base-uncased")
        self.file_name_extractor : FileNameExtractor = FileNameExtractor()

    def query(self, user_query: str, use_retrieval: bool = True) -> dict:
        """
        Full RAG flow: Retrieve → Augment → Generate (based on retrieval choice).
        """

        intent = self.query_classifier.predict(user_query)

        if use_retrieval:
            print(f"\n Retrieving context for query: {user_query}")

            files = self.file_name_extractor.extract(user_query)
            if not files:
                retrieved_chunks = self.retriever.retrieve(user_query)
            else:
                retrieved_chunks = []
                for file in files:
                    retrievedchunk_from_file = self.retriever.file_retrieval(file)
                    retrieved_chunks += retrievedchunk_from_file

            print(f"_______\n{retrieved_chunks}\n____")

            if not retrieved_chunks:
                print("No relevant chunks found. Falling back to non-retrieval generation.")
                return self.generator.generate_without_retrieval(user_query, intent)

            print(f"Retrieved {len(retrieved_chunks)} chunks. Augmenting context...")

            augmented = self.augmenter.augment(user_query, retrieved_chunks)
            print(f"Context built with {augmented['token_count']} tokens.")

            print(f"Generating response using intent: '{intent}'...")
            result = self.generator.generate_with_retrieval(
                query=user_query,
                intent=intent,
                context=augmented["context"],
                sources=augmented["sources"]
            )
        else:
            print(f"\nGenerating direct response for query: {user_query}")
            result = self.generator.generate_without_retrieval(user_query, intent)

        return result


# if __name__ == "__main__":
#     folder = input("Enter the path to your docset folder: ").strip()
#     if not os.path.exists(folder):
#         print("Invalid folder path.")
#     else:
#         rag = RAGPipeline(docset_folder=folder)

#         while True:
#             query = input("\nAsk a question (or type '<exit>' to quit): ").strip()
#             if query.lower() == "exit":
#                 break
#             response = rag.query(query, intent="factual")
#             print(f"\nSmartScholar Answer:\n{response.get('answer', response)}\n")
