import os
import pickle
import random

class ModelLoader:
    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelLoader, cls).__new__(cls)
            cls._instance._load_model()
        return cls._instance

    def _load_model(self):
        """Lazy load the model. Mocking a RandomForest for now."""
        # Check if a model file actually exists (Phase 5 compliance)
        model_path = os.path.join(os.path.dirname(__file__), "saved_models", "recommendation_rf.pkl")
        if os.path.exists(model_path):
            with open(model_path, 'rb') as f:
                self._model = pickle.load(f)
            print("Loaded real model from", model_path)
        else:
            print("No model found at", model_path, "- Using Mock Model Proxy")
            self._model = self._mock_model_proxy()

    def _mock_model_proxy(self):
        """Returns a mock class that responds to predict_proba"""
        class MockModel:
            def predict_proba(self, features):
                # features: [age, bmi, disease_count, food_calories, food_sugar, ...]
                # Return a random probability for demonstration of architecture
                prob = random.uniform(0.4, 0.95)
                return [[1 - prob, prob]]
        return MockModel()

    def get_model(self):
        return self._model
