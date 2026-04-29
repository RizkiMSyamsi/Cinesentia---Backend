"""
ML inference service — loads .h5 model, tokenizer, label encoder once as singleton.
"""

import os
import pickle
import logging

import numpy as np
from nltk.sentiment.vader import SentimentIntensityAnalyzer

logger = logging.getLogger(__name__)


class MLService:
    """Singleton service for ML model inference."""

    _instance = None

    def __init__(self):
        ml_dir = os.path.join(os.path.dirname(__file__), "..", "ml")

        model_path = os.path.join(ml_dir, "lstm_cnn_sentiment_model_80_20.h5")
        tokenizer_path = os.path.join(ml_dir, "tokenizer.pkl")
        encoder_path = os.path.join(ml_dir, "label_encoder.pkl")

        # Check if model files exist
        if not os.path.exists(model_path):
            logger.warning(
                f"Model file not found at {model_path}. "
                "ML inference will not be available until model files are placed in app/ml/."
            )
            self.model = None
            self.tokenizer = None
            self.label_encoder = None
        else:
            from tensorflow.keras.models import load_model

            logger.info("Loading ML model and tokenizer...")
            self.model = load_model(model_path)
            with open(tokenizer_path, "rb") as f:
                self.tokenizer = pickle.load(f)
            with open(encoder_path, "rb") as f:
                self.label_encoder = pickle.load(f)
            logger.info("ML model loaded successfully.")

        # VADER is always available
        import nltk
        nltk.download("vader_lexicon", quiet=True)
        self.vader = SentimentIntensityAnalyzer()

    @classmethod
    def get_instance(cls):
        """Get or create the singleton MLService instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def vader_sentiment(self, text):
        """Get VADER sentiment label from compound score."""
        score = self.vader.polarity_scores(text)["compound"]
        if score >= 0.05:
            return "positive", score
        elif score <= -0.05:
            return "negative", score
        return "neutral", score

    def predict(self, original_text, preprocessed_text, max_length=100):
        """
        Run both model and VADER prediction on a comment.
        
        Returns dict with model and VADER results.
        """
        # VADER on original and preprocessed
        vader_orig_label, vader_orig_score = self.vader_sentiment(original_text)
        vader_proc_label, vader_proc_score = self.vader_sentiment(preprocessed_text)

        result = {
            "vader_original_score": float(vader_orig_score),
            "vader_original_label": vader_orig_label,
            "vader_processed_score": float(vader_proc_score),
            "vader_processed_label": vader_proc_label,
        }

        # Model prediction (if model is loaded)
        if self.model and self.tokenizer and self.label_encoder:
            from tensorflow.keras.preprocessing.sequence import pad_sequences

            sequence = self.tokenizer.texts_to_sequences([preprocessed_text])
            padded = pad_sequences(sequence, maxlen=max_length)
            prediction = self.model.predict(padded, verbose=0)
            predicted_label = np.argmax(prediction, axis=1)[0]

            result["model_sentiment"] = self.label_encoder.inverse_transform(
                [predicted_label]
            )[0]
            result["model_confidence"] = float(np.max(prediction))
        else:
            # Fallback to VADER if model not available
            result["model_sentiment"] = vader_proc_label
            result["model_confidence"] = abs(vader_proc_score)

        return result
