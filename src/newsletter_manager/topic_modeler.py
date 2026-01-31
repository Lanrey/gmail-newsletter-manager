"""Topic modeling for newsletter categorization using LDA."""

import re
from pathlib import Path
from typing import Dict, List, Tuple

import joblib
import numpy as np
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.feature_extraction.text import CountVectorizer


class TopicModeler:
    """Topic modeling for newsletter categorization."""

    def __init__(self, n_topics: int = 10, min_df: int = 2, max_df: float = 0.7):
        """Initialize topic modeler.

        Args:
            n_topics: Number of topics to discover
            min_df: Minimum document frequency for terms
            max_df: Maximum document frequency for terms
        """
        self.n_topics = n_topics
        self.min_df = min_df
        self.max_df = max_df

        # Vectorizer to convert text to term frequencies
        self.vectorizer = CountVectorizer(
            max_features=1000,
            min_df=min_df,
            max_df=max_df,
            stop_words="english",
            ngram_range=(1, 2),
        )

        # LDA model
        self.lda_model = LatentDirichletAllocation(
            n_components=n_topics,
            random_state=42,
            max_iter=50,
            learning_method="online",
            n_jobs=-1,
        )

        # Topic labels (assigned after training)
        self.topic_labels: Dict[int, str] = {}
        self.is_trained = False

    def preprocess_text(self, text: str) -> str:
        """Clean and preprocess text for modeling.

        Args:
            text: Raw text to preprocess

        Returns:
            Cleaned text
        """
        if not text:
            return ""

        # Convert to lowercase
        text = text.lower()

        # Remove URLs
        text = re.sub(r"http\S+|www\.\S+", "", text)

        # Remove email addresses
        text = re.sub(r"\S+@\S+", "", text)

        # Remove special characters but keep spaces
        text = re.sub(r"[^a-z0-9\s]", " ", text)

        # Remove extra whitespace
        text = " ".join(text.split())

        return text

    def train(self, newsletter_data: List[Tuple[str, str, str]]) -> Dict[int, List[str]]:
        """Train topic model on newsletter data.

        Args:
            newsletter_data: List of (from_email, subject, snippet) tuples

        Returns:
            Dictionary of topic_id -> top words
        """
        if not newsletter_data:
            raise ValueError("No newsletter data provided for training")

        # Combine from_email, subject, and snippet for each newsletter
        documents = []
        for from_email, subject, snippet in newsletter_data:
            # Extract sender name from email
            sender = from_email.split("@")[0].replace(".", " ").replace("_", " ")

            # Combine all text
            text = f"{sender} {subject} {snippet}"
            cleaned = self.preprocess_text(text)
            documents.append(cleaned)

        # Transform documents to term frequencies
        doc_term_matrix = self.vectorizer.fit_transform(documents)

        # Train LDA model
        self.lda_model.fit(doc_term_matrix)
        self.is_trained = True

        # Get top words for each topic
        topic_words = self._get_topic_top_words(n_words=10)

        # Auto-assign topic labels based on top words
        self._auto_label_topics(topic_words)

        return topic_words

    def predict_topic(
        self, from_email: str, subject: str, snippet: str = ""
    ) -> Tuple[int, str, float]:
        """Predict topic for a newsletter.

        Args:
            from_email: Sender email address
            subject: Email subject
            snippet: Email snippet/preview text

        Returns:
            Tuple of (topic_id, topic_label, confidence)
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")

        # Prepare text
        sender = from_email.split("@")[0].replace(".", " ").replace("_", " ")
        text = f"{sender} {subject} {snippet}"
        cleaned = self.preprocess_text(text)

        # Transform and predict
        doc_vector = self.vectorizer.transform([cleaned])
        topic_distribution = self.lda_model.transform(doc_vector)[0]

        # Get most likely topic
        topic_id = int(np.argmax(topic_distribution))
        confidence = float(topic_distribution[topic_id])
        topic_label = self.topic_labels.get(topic_id, f"Topic_{topic_id}")

        return topic_id, topic_label, confidence

    def _get_topic_top_words(self, n_words: int = 10) -> Dict[int, List[str]]:
        """Get top words for each topic.

        Args:
            n_words: Number of top words to return per topic

        Returns:
            Dictionary of topic_id -> list of top words
        """
        feature_names = self.vectorizer.get_feature_names_out()
        topic_words = {}

        for topic_idx, topic in enumerate(self.lda_model.components_):
            top_word_indices = topic.argsort()[-n_words:][::-1]
            top_words = [feature_names[i] for i in top_word_indices]
            topic_words[topic_idx] = top_words

        return topic_words

    def _auto_label_topics(self, topic_words: Dict[int, List[str]]) -> None:
        """Automatically assign labels to topics based on top words.

        Args:
            topic_words: Dictionary of topic_id -> top words
        """
        # Keyword mapping for category detection
        category_keywords = {
            "Tech": [
                "tech",
                "software",
                "code",
                "developer",
                "engineering",
                "programming",
                "cloud",
                "api",
                "github",
                "python",
                "javascript",
                "data",
                "ai",
                "ml",
            ],
            "Business": [
                "business",
                "startup",
                "entrepreneur",
                "marketing",
                "sales",
                "revenue",
                "growth",
                "strategy",
                "company",
            ],
            "News": [
                "news",
                "daily",
                "weekly",
                "today",
                "update",
                "briefing",
                "headlines",
                "breaking",
            ],
            "Finance": [
                "finance",
                "investment",
                "stock",
                "market",
                "trading",
                "crypto",
                "money",
                "economics",
            ],
            "Design": [
                "design",
                "ui",
                "ux",
                "creative",
                "visual",
                "typography",
                "color",
                "layout",
            ],
            "Career": [
                "job",
                "career",
                "hiring",
                "opportunity",
                "position",
                "interview",
                "resume",
                "linkedin",
            ],
            "Product": [
                "product",
                "launch",
                "feature",
                "release",
                "update",
                "announcement",
            ],
        }

        for topic_id, words in topic_words.items():
            # Score each category
            category_scores = {}
            for category, keywords in category_keywords.items():
                score = sum(1 for word in words if any(kw in word for kw in keywords))
                if score > 0:
                    category_scores[category] = score

            # Assign label based on highest score
            if category_scores:
                best_category = max(category_scores, key=category_scores.get)
                self.topic_labels[topic_id] = best_category
            else:
                # Use first two words as label if no category matches
                label = "_".join(words[:2]).title()
                self.topic_labels[topic_id] = label

    def save_model(self, filepath: Path) -> None:
        """Save model to disk.

        Args:
            filepath: Path to save model
        """
        if not self.is_trained:
            raise ValueError("Cannot save untrained model")

        model_data = {
            "vectorizer": self.vectorizer,
            "lda_model": self.lda_model,
            "topic_labels": self.topic_labels,
            "n_topics": self.n_topics,
            "min_df": self.min_df,
            "max_df": self.max_df,
        }

        joblib.dump(model_data, filepath)

    @classmethod
    def load_model(cls, filepath: Path) -> "TopicModeler":
        """Load model from disk.

        Args:
            filepath: Path to load model from

        Returns:
            Loaded TopicModeler instance
        """
        if not filepath.exists():
            raise FileNotFoundError(f"Model file not found: {filepath}")

        model_data = joblib.load(filepath)

        # Create new instance
        modeler = cls(
            n_topics=model_data["n_topics"],
            min_df=model_data["min_df"],
            max_df=model_data["max_df"],
        )

        # Restore trained components
        modeler.vectorizer = model_data["vectorizer"]
        modeler.lda_model = model_data["lda_model"]
        modeler.topic_labels = model_data["topic_labels"]
        modeler.is_trained = True

        return modeler

    def get_topic_distribution(
        self, from_email: str, subject: str, snippet: str = ""
    ) -> Dict[str, float]:
        """Get full topic distribution for a newsletter.

        Args:
            from_email: Sender email address
            subject: Email subject
            snippet: Email snippet/preview text

        Returns:
            Dictionary of topic_label -> probability
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")

        # Prepare text
        sender = from_email.split("@")[0].replace(".", " ").replace("_", " ")
        text = f"{sender} {subject} {snippet}"
        cleaned = self.preprocess_text(text)

        # Transform and get distribution
        doc_vector = self.vectorizer.transform([cleaned])
        topic_distribution = self.lda_model.transform(doc_vector)[0]

        # Map to labels
        distribution = {}
        for topic_id, prob in enumerate(topic_distribution):
            label = self.topic_labels.get(topic_id, f"Topic_{topic_id}")
            distribution[label] = float(prob)

        return distribution
