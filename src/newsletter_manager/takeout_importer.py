"""Import Gmail Takeout MBOX files into the database."""

from __future__ import annotations

import hashlib
import mailbox
from datetime import datetime
from email.header import decode_header, make_header
from email.utils import parsedate_to_datetime

from .database import Database
from .newsletter_detector import NewsletterDetector


def _decode_header(value: str | None) -> str:
    if not value:
        return ""
    try:
        return str(make_header(decode_header(value)))
    except Exception:
        return value


def _parse_date(value: str | None) -> str:
    if not value:
        return datetime.now().isoformat()
    try:
        dt = parsedate_to_datetime(value)
        if dt is None:
            return datetime.now().isoformat()
        return dt.isoformat()
    except Exception:
        return datetime.now().isoformat()


def _extract_labels(msg) -> list[str]:
    labels_header = (
        msg.get("X-Gmail-Labels") or msg.get("X-GM-LABELS") or msg.get("X-Gmail-Labels".lower())
    )
    if not labels_header:
        return []
    return [part.strip() for part in labels_header.split(",") if part.strip()]


def _extract_message_id(msg) -> str:
    gm_id = msg.get("X-GM-MSGID") or msg.get("X-Gmail-Message-ID")
    if gm_id:
        return str(gm_id).strip()

    message_id = msg.get("Message-ID") or msg.get("Message-Id")
    if message_id:
        return message_id.strip("<> ")

    # Fallback: stable hash
    from_header = _decode_header(msg.get("From", ""))
    subject = _decode_header(msg.get("Subject", ""))
    date_str = _parse_date(msg.get("Date"))
    raw = f"{from_header}|{subject}|{date_str}"
    return f"mbox:{hashlib.sha1(raw.encode('utf-8')).hexdigest()}"


def import_mbox(
    mbox_path: str,
    detector: NewsletterDetector,
    db: Database,
    max_messages: int | None = None,
    dry_run: bool = False,
    progress_callback=None,
) -> tuple[int, int]:
    """Import a Gmail Takeout MBOX file.

    Returns:
        Tuple of (messages_processed, newsletters_found)
    """
    mbox = mailbox.mbox(mbox_path, factory=None, create=False)

    processed = 0
    newsletters_found = 0

    for msg in mbox:
        if max_messages and processed >= max_messages:
            break

        from_header = _decode_header(msg.get("From", ""))
        subject = _decode_header(msg.get("Subject", ""))
        date_iso = _parse_date(msg.get("Date"))
        labels = _extract_labels(msg)

        message_dict: dict = {
            "from": from_header,
            "subject": subject,
            "date": date_iso,
            "labels": labels,
        }

        is_newsletter, platform, _reasons = detector.is_newsletter(message_dict)
        if is_newsletter:
            sender_email = detector._get_from_email(message_dict)
            sender_name = detector._get_from_name(message_dict)
            category = detector.categorize_newsletter(sender_email, subject)

            newsletter_id = db.upsert_newsletter(
                sender_email=sender_email,
                sender_name=sender_name,
                category=category,
                platform=platform,
                first_seen=date_iso,
                last_seen=date_iso,
                auto_categorized=bool(category),
            )

            message_id = _extract_message_id(msg)
            is_read = "UNREAD" not in labels

            if not dry_run:
                db.add_message(
                    message_id=message_id,
                    newsletter_id=newsletter_id,
                    subject=subject,
                    received_date=date_iso,
                    is_read=is_read,
                    labels=labels,
                )

            newsletters_found += 1

        processed += 1

        if progress_callback:
            progress_callback(processed, newsletters_found)

    return processed, newsletters_found
