import os
import torch
import joblib
from transformers import BertTokenizer, BertModel
from sklearn.preprocessing import LabelEncoder

class QueryClassifier:
    def __init__(self, model_path="local/query_classifier_model.pkl", bert_model="bert-base-uncased"):
        self.model_path = model_path
        self.bert_model = bert_model
        self.tokenizer, self.bert = self.load_bert()
        self.label_encoder = LabelEncoder()
        self.model = self.load_model()

    def load_bert(self):
        """Load BERT tokenizer and model, downloading if not found."""
        local_path = "local"
        os.makedirs(local_path, exist_ok=True)
        
        tokenizer = BertTokenizer.from_pretrained(self.bert_model, cache_dir=local_path)
        bert = BertModel.from_pretrained(self.bert_model, cache_dir=local_path)
        return tokenizer, bert

    def encode_query(self, query):
        """Convert query into BERT embeddings."""
        tokens = self.tokenizer(query, return_tensors="pt", padding=True, truncation=True, max_length=64)
        with torch.no_grad():
            output = self.bert(**tokens)
        return output.last_hidden_state[:, 0, :].squeeze().numpy()  # Extract CLS token representation

    def load_model(self):
        """Load trained model."""
        if os.path.exists(self.model_path):
            print("Loading trained model...")
            return joblib.load(self.model_path)
        else:
            raise FileNotFoundError(f"Model not found at {self.model_path}. Please train the model first.")

    def predict(self, query):
        """Predict the query type."""
        embedding = self.encode_query(query).reshape(1, -1)
        label_index = self.model.predict(embedding)[0]
        
        # Label Mapping: {0: 'conceptual', 1: 'explanatory', 2: 'factual', 3: 'general', 4: 'technical'}
        return label_index


# Usage Example (In a separate file, not here)
if __name__ == "__main__":
    classifier = QueryClassifier()
    test_query = "How do economic policies like fiscal stimulus, quantitative easing, and interest rate adjustments influence inflation, unemployment, and GDP growth, and what are the trade-offs and risks associated with each approach in different economic contexts?"
    predicted_label = classifier.predict(test_query)
    print(f"Predicted Query Type: {predicted_label}")
