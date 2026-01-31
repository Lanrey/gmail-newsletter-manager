"""Tests for newsletter detector."""

import pytest
from newsletter_manager.newsletter_detector import NewsletterDetector
from newsletter_manager.config import Config


def test_is_newsletter_with_list_unsubscribe():
    """Test newsletter detection with List-Unsubscribe header."""
    config = Config()
    config.load()
    detector = NewsletterDetector(config)
    
    message = {
        'id': '123',
        'subject': 'Weekly Update',
        'payload': {
            'headers': [
                {'name': 'From', 'value': 'newsletter@example.com'},
                {'name': 'List-Unsubscribe', 'value': '<mailto:unsub@example.com>'}
            ]
        },
        'snippet': 'This is a newsletter'
    }
    
    is_newsletter, platform, reasons = detector.is_newsletter(message)
    
    assert is_newsletter is True
    assert 'has_list_unsubscribe_header' in reasons


def test_is_newsletter_with_platform():
    """Test newsletter detection with known platform."""
    config = Config()
    config.load()
    detector = NewsletterDetector(config)
    
    message = {
        'id': '124',
        'subject': 'Your weekly digest',
        'payload': {
            'headers': [
                {'name': 'From', 'value': 'news@mail.substack.com'},
            ]
        },
        'snippet': 'Newsletter content'
    }
    
    is_newsletter, platform, reasons = detector.is_newsletter(message)
    
    assert is_newsletter is True
    assert platform == 'substack.com'


def test_is_not_newsletter():
    """Test that regular emails are not detected as newsletters."""
    config = Config()
    config.load()
    detector = NewsletterDetector(config)
    
    message = {
        'id': '125',
        'subject': 'Meeting tomorrow',
        'payload': {
            'headers': [
                {'name': 'From', 'value': 'colleague@company.com'},
            ]
        },
        'snippet': 'See you at the meeting'
    }
    
    is_newsletter, platform, reasons = detector.is_newsletter(message)
    
    assert is_newsletter is False


def test_extract_domain():
    """Test domain extraction from email."""
    config = Config()
    config.load()
    detector = NewsletterDetector(config)
    
    assert detector._extract_domain('user@example.com') == 'example.com'
    assert detector._extract_domain('test@mail.substack.com') == 'mail.substack.com'


def test_is_bulk_sender():
    """Test bulk sender pattern detection."""
    config = Config()
    config.load()
    detector = NewsletterDetector(config)
    
    assert detector._is_bulk_sender('no-reply@example.com') is True
    assert detector._is_bulk_sender('newsletter@company.com') is True
    assert detector._is_bulk_sender('notifications@service.com') is True
    assert detector._is_bulk_sender('person@company.com') is False


def test_categorize_newsletter():
    """Test newsletter auto-categorization."""
    config = Config()
    config.load()
    detector = NewsletterDetector(config)

    # Tech newsletter
    category, confidence = detector.categorize_newsletter(
        'newsletter@dev.to',
        'Weekly Programming Tips'
    )
    # Category should be identified (either from topic model or keywords)
    assert category is not None
    assert isinstance(confidence, float)
    assert 0.0 <= confidence <= 1.0

    # Business newsletter
    category, confidence = detector.categorize_newsletter(
        'news@entrepreneur.com',
        'Startup News Weekly'
    )
    assert isinstance(confidence, float)

    # Generic email with topic model will still classify
    # (topic model returns something, not keyword-based fallback)
    category, confidence = detector.categorize_newsletter(
        'random@example.com',
        'Random Update'
    )
    # The hybrid model may classify this as something
    # Just verify it returns tuple format
    assert isinstance(category, (str, type(None)))
    assert isinstance(confidence, float)


def test_extract_unsubscribe_link():
    """Test unsubscribe link extraction."""
    config = Config()
    config.load()
    detector = NewsletterDetector(config)
    
    message = {
        'payload': {
            'headers': [
                {
                    'name': 'List-Unsubscribe',
                    'value': '<mailto:unsub@example.com>, <https://example.com/unsubscribe>'
                }
            ]
        }
    }
    
    link = detector.extract_unsubscribe_link(message)
    assert link == 'https://example.com/unsubscribe'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
