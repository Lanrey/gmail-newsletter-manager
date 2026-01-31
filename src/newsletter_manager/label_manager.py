"""Label management for Gmail."""

from typing import Dict, List, Optional

from .gogcli_wrapper import GogCLI


class LabelManager:
    """Manages Gmail labels and label hierarchies."""

    def __init__(self, gog: GogCLI):
        """Initialize label manager.

        Args:
            gog: GogCLI instance
        """
        self.gog = gog
        self._labels_cache: Optional[List[Dict]] = None
        self._labels_by_name: Optional[Dict[str, Dict]] = None

    def refresh_labels(self) -> None:
        """Refresh labels cache from Gmail."""
        self._labels_cache = self.gog.list_labels()
        self._labels_by_name = {label["name"]: label for label in self._labels_cache}

    def get_labels(self, refresh: bool = False) -> List[Dict]:
        """Get all labels.

        Args:
            refresh: Whether to refresh from Gmail

        Returns:
            List of label dictionaries
        """
        if refresh or self._labels_cache is None:
            self.refresh_labels()
        return self._labels_cache or []

    def get_label_by_name(self, name: str, refresh: bool = False) -> Optional[Dict]:
        """Get label by name.

        Args:
            name: Label name
            refresh: Whether to refresh from Gmail

        Returns:
            Label dictionary or None
        """
        if refresh or self._labels_by_name is None:
            self.refresh_labels()
        return self._labels_by_name.get(name) if self._labels_by_name else None

    def label_exists(self, name: str) -> bool:
        """Check if a label exists.

        Args:
            name: Label name

        Returns:
            True if label exists
        """
        return self.get_label_by_name(name) is not None

    def create_label_hierarchy(self, path: str) -> Dict:
        """Create a hierarchical label (e.g., "Newsletters/Tech/AI").

        Creates all parent labels if they don't exist.

        Args:
            path: Label path with / separators

        Returns:
            The final (leaf) label dictionary
        """
        parts = path.split("/")

        # Create each level of the hierarchy
        for i in range(1, len(parts) + 1):
            label_name = "/".join(parts[:i])

            if not self.label_exists(label_name):
                try:
                    self.gog.create_label(label_name)
                except Exception:
                    # Label might have been created by another process, that's OK
                    pass
                # Invalidate cache
                self._labels_cache = None
                self._labels_by_name = None

        # Return the final label
        return self.get_label_by_name(path, refresh=True)

    def get_or_create_label(self, name: str) -> Dict:
        """Get existing label or create if it doesn't exist.

        Args:
            name: Label name

        Returns:
            Label dictionary
        """
        label = self.get_label_by_name(name)
        if label:
            return label

        # Create with hierarchy support
        return self.create_label_hierarchy(name)

    def create_newsletter_labels(self, categories: List[str]) -> Dict[str, Dict]:
        """Create standard newsletter label hierarchy.

        Creates labels like:
        - Newsletters
        - Newsletters/Tech
        - Newsletters/Business
        - etc.

        Args:
            categories: List of category names

        Returns:
            Dictionary mapping label names to label dictionaries
        """
        labels = {}

        # Create root Newsletters label
        root_label = self.get_or_create_label("Newsletters")
        labels["Newsletters"] = root_label

        # Create category labels
        for category in categories:
            label_name = f"Newsletters/{category}"
            label = self.get_or_create_label(label_name)
            labels[label_name] = label

        return labels

    def get_newsletter_label_name(
        self, category: Optional[str] = None, sender_name: Optional[str] = None
    ) -> str:
        """Generate label name for a newsletter.

        Args:
            category: Newsletter category
            sender_name: Newsletter sender name

        Returns:
            Label name string
        """
        parts = ["Newsletters"]

        if category:
            parts.append(category)

        if sender_name:
            # Clean sender name for label
            clean_name = self._clean_label_name(sender_name)
            parts.append(clean_name)

        return "/".join(parts)

    def _clean_label_name(self, name: str) -> str:
        """Clean a string for use as a label name.

        Args:
            name: Raw name

        Returns:
            Cleaned label name
        """
        # Remove special characters, limit length
        cleaned = "".join(c for c in name if c.isalnum() or c in (" ", "-", "_"))
        cleaned = cleaned.strip()

        # Convert spaces to hyphens
        cleaned = cleaned.replace(" ", "-")

        # Limit length
        if len(cleaned) > 50:
            cleaned = cleaned[:50]

        return cleaned

    def apply_label_to_messages(self, message_ids: List[str], label_name: str) -> None:
        """Apply a label to multiple messages.

        Args:
            message_ids: List of message IDs
            label_name: Label name to apply
        """
        # Ensure label exists
        label = self.get_or_create_label(label_name)
        label_id = label.get("id")

        if not label_id:
            raise ValueError(f"Could not get ID for label: {label_name}")

        # Batch modify messages
        if len(message_ids) > 0:
            self.gog.batch_modify_messages(message_ids, add_labels=[label_id])

    def get_messages_with_label(self, label_name: str) -> List[Dict]:
        """Get all messages with a specific label.

        Args:
            label_name: Label name

        Returns:
            List of message dictionaries
        """
        label = self.get_label_by_name(label_name)
        if not label:
            return []

        label_id = label.get("id")
        query = f"label:{label_id}"

        return self.gog.search_messages(query)

    def list_newsletter_labels(self) -> List[Dict]:
        """Get all labels under Newsletters hierarchy.

        Returns:
            List of newsletter label dictionaries
        """
        all_labels = self.get_labels()
        return [label for label in all_labels if label.get("name", "").startswith("Newsletters/")]

    def organize_newsletter_labels(self) -> Dict[str, List[Dict]]:
        """Organize newsletter labels by category.

        Returns:
            Dictionary mapping categories to label lists
        """
        newsletter_labels = self.list_newsletter_labels()
        organized = {}

        for label in newsletter_labels:
            name = label.get("name", "")
            parts = name.split("/")

            if len(parts) >= 2:
                category = parts[1]  # e.g., "Tech" from "Newsletters/Tech/..."

                if category not in organized:
                    organized[category] = []

                organized[category].append(label)

        return organized
