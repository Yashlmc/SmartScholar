import os
import torch
import joblib
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from transformers import BertTokenizer, BertModel

class QueryClassifierTrainer:
    def __init__(self, model_path="local/query_classifier_model.pkl", bert_model="bert-base-uncased"):
        self.model_path = model_path
        self.bert_model = bert_model
        self.tokenizer, self.bert = self.load_bert()
        self.label_encoder = LabelEncoder()

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

    def train_model(self):
        """Train the query classifier using ML on top of BERT embeddings."""
        
        dataset = pd.read_csv("dataset.csv")
        print(dataset.head())

        # Define categories explicitly to ensure consistent encoding
        categories = ["factual", "explanatory", "technical", "conceptual", "general"]
        self.label_encoder.fit(categories)  # Fit label encoder with fixed category order
        
        X = [self.encode_query(q) for q in dataset["query"]]
        y = self.label_encoder.transform(dataset["category"])  # Encode using fixed encoder
        
        # print(y)  # Debugging check

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        classifier = LogisticRegression(max_iter=500)
        classifier.fit(X_train, y_train)

        joblib.dump(classifier, self.model_path)
        print("Model trained and saved successfully!")
        return classifier


if __name__ == "__main__":
    trainer = QueryClassifierTrainer()
    trainer.train_model()  # Train the model and save it
