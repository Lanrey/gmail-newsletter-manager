"""Newsletter detection and analysis."""

import re
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional, Tuple


class NewsletterDetector:
    """Detects newsletters from email messages."""

    NEWSLETTER_INDICATORS = [
        "list-unsubscribe",
        "newsletter",
        "digest",
        "weekly",
        "daily",
        "monthly",
        "update",
        "roundup",
        "briefing",
        "subscription",
        "mailing list",
    ]

    NEWSLETTER_PLATFORMS = [
        "substack.com",
        "beehiiv.com",
        "mailchimp.com",
        "constantcontact.com",
        "convertkit.com",
        "buttondown.email",
        "ghost.io",
        "revue.com",
        "sendfox.com",
        "mailerlite.com",
        "sendgrid.net",
        "list-manage.com",
        "campaignmonitor.com",
    ]

    def __init__(self, config):
        """Initialize detector with configuration."""
        self.config = config
        self.patterns = config.get_newsletter_patterns()
        self.platforms = config.get_known_platforms()

    def is_newsletter(self, message: Dict) -> Tuple[bool, Optional[str], List[str]]:
        """Determine if a message is a newsletter.

        Args:
            message: Message dictionary from gogcli (can be thread or full message)

        Returns:
            Tuple of (is_newsletter, platform, reasons)
        """
        reasons = []
        platform = None

        # Check if this is a thread object (from search) or full message
        is_thread = "from" in message and "payload" not in message

        # Extract message details
        from_email = self._get_from_email(message)
        from_domain = self._extract_domain(from_email)
        subject = message.get("subject", "").lower()

        # For full messages, check List-Unsubscribe header
        if not is_thread:
            headers = self._get_headers(message)
            if "list-unsubscribe" in headers:
                reasons.append("has_list_unsubscribe_header")

        # Check sender domain against known platforms
        for platform_domain in self.platforms + self.NEWSLETTER_PLATFORMS:
            if platform_domain in from_domain:
                reasons.append(f"from_platform:{platform_domain}")
                platform = platform_domain
                break

        # Check subject line for newsletter patterns
        for pattern in self.patterns + self.NEWSLETTER_INDICATORS:
            if pattern.lower() in subject:
                reasons.append(f"subject_contains:{pattern}")

        # Check for typical newsletter structure keywords
        newsletter_keywords = [
            "unsubscribe",
            "view in browser",
            "preference center",
            "manage subscription",
            "view online",
        ]

        # Check snippet/body if available (thread format has labels we can check)
        if is_thread:
            labels = message.get("labels", [])
            # Promotional emails often indicate newsletters
            if "CATEGORY_PROMOTIONS" in labels:
                reasons.append("promotional_category")
            if "CATEGORY_UPDATES" in labels:
                reasons.append("updates_category")

        snippet = message.get("snippet", "").lower() if "snippet" in message else ""
        for keyword in newsletter_keywords:
            if keyword in snippet:
                reasons.append(f"body_contains:{keyword}")

        # Check for bulk sender patterns
        if self._is_bulk_sender(from_email):
            reasons.append("bulk_sender_pattern")

        # Determine if it's a newsletter (need at least 2 indicators or 1 strong one)
        is_newsletter = (
            len(reasons) >= 2
            or "has_list_unsubscribe_header" in reasons
            or any("from_platform:" in r for r in reasons)
        )

        return is_newsletter, platform, reasons

        return is_newsletter, platform, reasons

    def _get_headers(self, message: Dict) -> Dict[str, str]:
        """Extract headers from message."""
        headers_dict = {}

        if "payload" in message and "headers" in message["payload"]:
            for header in message["payload"]["headers"]:
                name = header.get("name", "").lower()
                value = header.get("value", "")
                headers_dict[name] = value

        return headers_dict

    def _get_from_email(self, message: Dict) -> str:
        """Extract sender email from message."""
        # Handle thread format from gog search (has 'from' field directly)
        if "from" in message and "payload" not in message:
            from_header = message["from"]
            # Extract email from "Name <email@domain.com>" format
            match = re.search(r"<([^>]+)>", from_header)
            if match:
                return match.group(1).lower()
            return from_header.strip("<>").lower()

        # Handle full message format (has payload.headers)
        headers = self._get_headers(message)
        from_header = headers.get("from", "")

        # Extract email from "Name <email@domain.com>" format
        match = re.search(r"<([^>]+)>", from_header)
        if match:
            return match.group(1).lower()

        # If no angle brackets, assume it's just the email
        return from_header.strip("<>").lower()

    def _get_from_name(self, message: Dict) -> Optional[str]:
        """Extract sender name from message."""
        # Handle thread format from gog search
        if "from" in message and "payload" not in message:
            from_header = message["from"]
            # Extract name from "Name <email@domain.com>" format
            match = re.match(r"^([^<]+)<", from_header)
            if match:
                return match.group(1).strip()
            return None

        # Handle full message format
        headers = self._get_headers(message)
        from_header = headers.get("from", "")

        # Extract name from "Name <email@domain.com>" format
        match = re.match(r"^([^<]+)<", from_header)
        if match:
            return match.group(1).strip()

        return None

    def _extract_domain(self, email: str) -> str:
        """Extract domain from email address."""
        if "@" in email:
            return email.split("@")[1].lower()
        return ""

    def _is_bulk_sender(self, email: str) -> bool:
        """Check if email matches bulk sender patterns."""
        bulk_patterns = [
            r"no-?reply@",
            r"newsletter@",
            r"notifications?@",
            r"digest@",
            r"updates?@",
            r"news@",
            r"hello@",
            r"hi@",
            r"team@",
        ]

        for pattern in bulk_patterns:
            if re.search(pattern, email, re.IGNORECASE):
                return True

        return False

    def analyze_sender_frequency(self, messages: List[Dict]) -> Dict[str, Dict]:
        """Analyze sender frequency to identify potential newsletters.

        Args:
            messages: List of messages

        Returns:
            Dictionary mapping sender email to stats
        """
        sender_stats = defaultdict(lambda: {"count": 0, "dates": [], "subjects": [], "name": None})

        for message in messages:
            email = self._get_from_email(message)
            date_str = self._get_date(message)
            subject = message.get("subject", "")
            name = self._get_from_name(message)

            sender_stats[email]["count"] += 1
            sender_stats[email]["dates"].append(date_str)
            sender_stats[email]["subjects"].append(subject)
            if name:
                sender_stats[email]["name"] = name

        # Calculate frequency
        for _email, stats in sender_stats.items():
            if len(stats["dates"]) >= 2:
                dates = sorted(
                    [datetime.fromisoformat(d.replace("Z", "+00:00")) for d in stats["dates"]]
                )
                date_range = (dates[-1] - dates[0]).days
                if date_range > 0:
                    stats["frequency"] = len(dates) / (date_range / 30)  # emails per month
                else:
                    stats["frequency"] = 0
            else:
                stats["frequency"] = 0

        return dict(sender_stats)

    def _get_date(self, message: Dict) -> str:
        """Extract date from message."""
        # Handle thread format from gog search (has 'date' field directly)
        if "date" in message and "payload" not in message:
            date_str = message["date"]
            try:
                # Parse "2026-01-30 16:10" format and convert to ISO
                dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
                return dt.isoformat()
            except (ValueError, TypeError):
                return date_str

        # Try internalDate first (milliseconds since epoch)
        if "internalDate" in message:
            timestamp = int(message["internalDate"]) / 1000
            return datetime.fromtimestamp(timestamp).isoformat()

        # Fall back to Date header
        headers = self._get_headers(message)
        date_str = headers.get("date", "")

        if date_str:
            # Simple ISO format extraction (gogcli should provide this)
            return date_str

        return datetime.now().isoformat()

    def categorize_newsletter(self, sender_email: str, subject: str = "") -> Optional[str]:
        """Auto-categorize a newsletter based on sender and subject.

        Args:
            sender_email: Sender email address
            subject: Email subject

        Returns:
            Category name or None
        """
        categories = self.config.get_categories()

        sender_lower = sender_email.lower()
        subject_lower = subject.lower()

        # Score each category
        category_scores = defaultdict(int)

        for category, rules in categories.items():
            # Check domains
            for domain in rules.get("domains", []):
                if domain in sender_lower:
                    category_scores[category] += 5

            # Check keywords in subject
            for keyword in rules.get("keywords", []):
                if keyword.lower() in subject_lower:
                    category_scores[category] += 2
                if keyword.lower() in sender_lower:
                    category_scores[category] += 1

        # Return category with highest score if above threshold
        if category_scores:
            best_category = max(category_scores.items(), key=lambda x: x[1])
            if best_category[1] >= 3:  # Minimum score threshold
                return best_category[0]

        return None

    def extract_unsubscribe_link(self, message: Dict) -> Optional[str]:
        """Extract unsubscribe link from message.

        Args:
            message: Message dictionary

        Returns:
            Unsubscribe URL or None
        """
        headers = self._get_headers(message)

        # Check List-Unsubscribe header
        list_unsub = headers.get("list-unsubscribe", "")

        # Extract HTTP URL from List-Unsubscribe header
        # Format can be: <mailto:...>, <http://...> or just http://...
        http_match = re.search(r"<?(https?://[^>,\s]+)>?", list_unsub)
        if http_match:
            return http_match.group(1)

        return None
