import json
import os
import pickle
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
from mcp.server.fastmcp import FastMCP

# Initialize MCP server
mcp = FastMCP("Machine Learning Integration")

# Create a directory for storing ML models
MODEL_DIR = Path(os.path.expanduser("~")) / "mcp_ml_models"
MODEL_DIR.mkdir(exist_ok=True)

# Default path for a simple trained model
DEFAULT_MODEL_PATH = MODEL_DIR / "sentiment_classifier.pkl"


# Simple text preprocessing function
def preprocess_text(text: str) -> List[float]:
    """
    Convert text to a simple numerical feature vector
    This is a very basic implementation for demonstration purposes
    """
    # Count various types of characters
    features = []
    features.append(len(text))  # Text length
    features.append(
        sum(1 for c in text if c.isupper()) / max(len(text), 1)
    )  # Ratio of uppercase
    features.append(
        sum(1 for c in text if c in "!?,.") / max(len(text), 1)
    )  # Ratio of punctuation

    # Some basic sentiment word counting
    positive_words = ["good", "great", "excellent", "amazing", "love", "happy", "best"]
    negative_words = ["bad", "terrible", "awful", "worst", "hate", "sad", "poor"]

    text_lower = text.lower()
    features.append(
        sum(text_lower.count(word) for word in positive_words)
        / max(len(text.split()), 1)
    )
    features.append(
        sum(text_lower.count(word) for word in negative_words)
        / max(len(text.split()), 1)
    )

    return features


# Create a very simple sentiment classifier model
class SimpleSentimentClassifier:
    """A very simple sentiment classifier for demonstration purposes"""

    def __init__(self):
        self.weights = np.array([0.1, 0.4, -0.1, 0.7, -0.8])  # Random initial weights
        self.bias = 0.0

    def predict(self, features: List[float]) -> float:
        """Predict sentiment score (-1 to 1)"""
        features_array = np.array(features)
        return np.tanh(np.dot(features_array, self.weights) + self.bias)

    def train(self, texts: List[str], labels: List[float]) -> Dict[str, float]:
        """
        Train the model on labeled data

        Args:
            texts: List of text samples
            labels: List of sentiment labels (-1 to 1)

        Returns:
            Dictionary with training metrics
        """
        features = [preprocess_text(text) for text in texts]
        features_array = np.array(features)
        labels_array = np.array(labels)

        # Very simple gradient descent (for demonstration)
        learning_rate = 0.01
        n_epochs = 100
        n_samples = len(texts)

        training_loss = []

        for epoch in range(n_epochs):
            # Forward pass
            predictions = np.tanh(np.dot(features_array, self.weights) + self.bias)

            # Compute loss (MSE)
            loss = np.mean((predictions - labels_array) ** 2)
            training_loss.append(loss)

            # Backward pass (gradient descent)
            d_weights = (
                2 * np.dot(features_array.T, (predictions - labels_array)) / n_samples
            )
            d_bias = 2 * np.mean(predictions - labels_array)

            # Update parameters
            self.weights -= learning_rate * d_weights
            self.bias -= learning_rate * d_bias

        # Return training metrics
        return {
            "initial_loss": training_loss[0],
            "final_loss": training_loss[-1],
            "epochs": n_epochs,
            "samples": n_samples,
        }

    def evaluate(self, texts: List[str], labels: List[float]) -> Dict[str, float]:
        """
        Evaluate the model on labeled data

        Args:
            texts: List of text samples
            labels: List of sentiment labels (-1 to 1)

        Returns:
            Dictionary with evaluation metrics
        """
        features = [preprocess_text(text) for text in texts]
        predictions = [self.predict(feature) for feature in features]

        # Compute metrics
        mse = np.mean((np.array(predictions) - np.array(labels)) ** 2)
        mae = np.mean(np.abs(np.array(predictions) - np.array(labels)))

        # Compute accuracy for binary classification (thresholded at 0)
        binary_predictions = [1 if p > 0 else -1 for p in predictions]
        binary_labels = [1 if l > 0 else -1 for l in labels]
        accuracy = np.mean(np.array(binary_predictions) == np.array(binary_labels))

        return {
            "mse": float(mse),
            "mae": float(mae),
            "binary_accuracy": float(accuracy),
        }


# Initialize or load a model
def get_model() -> SimpleSentimentClassifier:
    """Get the trained model, or create and train a new one if it doesn't exist"""
    if os.path.exists(DEFAULT_MODEL_PATH):
        try:
            with open(DEFAULT_MODEL_PATH, "rb") as f:
                return pickle.load(f)
        except Exception:
            pass  # Fall back to creating a new model

    # Create and train a simple model with some example data
    model = SimpleSentimentClassifier()

    # Simple training data
    texts = [
        "I love this product, it's amazing!",
        "This is great, very happy with my purchase.",
        "Excellent service and quality.",
        "Not bad, but could be better.",
        "This was a terrible experience, very disappointed.",
        "Awful product, don't waste your money.",
        "The quality is poor and it broke quickly.",
        "It's okay, nothing special.",
    ]

    # Sentiment scores from -1 (negative) to 1 (positive)
    labels = [0.9, 0.8, 0.9, 0.0, -0.8, -0.9, -0.7, 0.0]

    # Train the model
    model.train(texts, labels)

    # Save the model
    with open(DEFAULT_MODEL_PATH, "wb") as f:
        pickle.dump(model, f)

    return model


# MCP tools for machine learning
@mcp.tool()
def predict_sentiment(text: str) -> str:
    """
    Predict sentiment score for a text using a trained model

    Args:
        text: The text to analyze
    """
    try:
        model = get_model()
        features = preprocess_text(text)
        sentiment_score = model.predict(features)

        # Convert score to a human-readable result
        if sentiment_score > 0.5:
            sentiment = "Very Positive"
        elif sentiment_score > 0.0:
            sentiment = "Positive"
        elif sentiment_score > -0.5:
            sentiment = "Negative"
        else:
            sentiment = "Very Negative"

        return json.dumps(
            {
                "text": text,
                "sentiment_score": float(sentiment_score),
                "sentiment": sentiment,
            },
            indent=2,
        )
    except Exception as e:
        return f"Error predicting sentiment: {str(e)}"


@mcp.tool()
def batch_predict_sentiment(texts: List[str]) -> str:
    """
    Predict sentiment scores for multiple texts

    Args:
        texts: List of texts to analyze
    """
    try:
        model = get_model()
        results = []

        for text in texts:
            features = preprocess_text(text)
            sentiment_score = float(model.predict(features))

            # Convert score to a human-readable result
            if sentiment_score > 0.5:
                sentiment = "Very Positive"
            elif sentiment_score > 0.0:
                sentiment = "Positive"
            elif sentiment_score > -0.5:
                sentiment = "Negative"
            else:
                sentiment = "Very Negative"

            results.append(
                {
                    "text": text,
                    "sentiment_score": sentiment_score,
                    "sentiment": sentiment,
                }
            )

        return json.dumps(results, indent=2)
    except Exception as e:
        return f"Error batch predicting sentiment: {str(e)}"


@mcp.tool()
def train_custom_model(texts: List[str], labels: List[float], model_name: str) -> str:
    """
    Train a custom sentiment model on user-provided data

    Args:
        texts: List of training text samples
        labels: List of sentiment labels between -1 and 1
        model_name: Name to save the model as
    """
    try:
        # Input validation
        if len(texts) != len(labels):
            return "Error: Number of texts and labels must match."

        if len(texts) < 5:
            return "Error: At least 5 training samples are required."

        for label in labels:
            if label < -1 or label > 1:
                return "Error: Labels must be between -1 and 1."

        if not model_name or not model_name.isalnum():
            return "Error: Model name must be alphanumeric."

        # Create and train the model
        model = SimpleSentimentClassifier()
        metrics = model.train(texts, labels)

        # Save the model
        model_path = MODEL_DIR / f"{model_name}.pkl"
        with open(model_path, "wb") as f:
            pickle.dump(model, f)

        return json.dumps(
            {
                "message": f"Model '{model_name}' trained successfully.",
                "samples": len(texts),
                "model_path": str(model_path),
                "initial_loss": metrics["initial_loss"],
                "final_loss": metrics["final_loss"],
            },
            indent=2,
        )
    except Exception as e:
        return f"Error training model: {str(e)}"


@mcp.tool()
def evaluate_model(
    texts: List[str], labels: List[float], model_name: Optional[str] = None
) -> str:
    """
    Evaluate a sentiment model on test data

    Args:
        texts: List of test text samples
        labels: List of true sentiment labels between -1 and 1
        model_name: Name of the model to evaluate (default: use the default model)
    """
    try:
        # Input validation
        if len(texts) != len(labels):
            return "Error: Number of texts and labels must match."

        if len(texts) < 3:
            return "Error: At least 3 evaluation samples are required."

        for label in labels:
            if label < -1 or label > 1:
                return "Error: Labels must be between -1 and 1."

        # Load the model
        if model_name:
            model_path = MODEL_DIR / f"{model_name}.pkl"
            if not os.path.exists(model_path):
                return f"Error: Model '{model_name}' not found."

            with open(model_path, "rb") as f:
                model = pickle.load(f)
        else:
            model = get_model()

        # Evaluate the model
        metrics = model.evaluate(texts, labels)

        return json.dumps(
            {
                "message": f"Model evaluated successfully on {len(texts)} samples.",
                "mse": metrics["mse"],
                "mae": metrics["mae"],
                "binary_accuracy": metrics["binary_accuracy"],
            },
            indent=2,
        )
    except Exception as e:
        return f"Error evaluating model: {str(e)}"


@mcp.tool()
def list_available_models() -> str:
    """List all available trained models"""
    try:
        models = [f.stem for f in MODEL_DIR.glob("*.pkl")]

        if not models:
            return "No trained models available."

        return json.dumps(
            {
                "available_models": models,
                "default_model": DEFAULT_MODEL_PATH.stem
                if os.path.exists(DEFAULT_MODEL_PATH)
                else None,
            },
            indent=2,
        )
    except Exception as e:
        return f"Error listing models: {str(e)}"


@mcp.resource("models://info")
def get_models_info() -> str:
    """Get information about all available ML models"""
    try:
        models = {}

        for model_path in MODEL_DIR.glob("*.pkl"):
            model_name = model_path.stem
            model_size = os.path.getsize(model_path)
            modified_time = os.path.getmtime(model_path)

            models[model_name] = {
                "file_path": str(model_path),
                "size_bytes": model_size,
                "last_modified": modified_time,
            }

        return json.dumps(
            {
                "models_count": len(models),
                "models_directory": str(MODEL_DIR),
                "models": models,
            },
            indent=2,
        )
    except Exception as e:
        return f"Error retrieving models info: {str(e)}"
