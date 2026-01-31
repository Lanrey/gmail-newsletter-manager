"""Tests for label manager."""

import pytest
from unittest.mock import Mock, MagicMock
from newsletter_manager.label_manager import LabelManager


def test_label_exists():
    """Test checking if a label exists."""
    mock_gog = Mock()
    mock_gog.list_labels.return_value = [
        {'id': '1', 'name': 'Newsletters'},
        {'id': '2', 'name': 'Newsletters/Tech'}
    ]
    
    manager = LabelManager(mock_gog)
    
    assert manager.label_exists('Newsletters') is True
    assert manager.label_exists('Newsletters/Tech') is True
    assert manager.label_exists('NonExistent') is False


def test_get_newsletter_label_name():
    """Test label name generation."""
    mock_gog = Mock()
    manager = LabelManager(mock_gog)
    
    # Just root
    assert manager.get_newsletter_label_name() == 'Newsletters'
    
    # With category
    assert manager.get_newsletter_label_name(category='Tech') == 'Newsletters/Tech'
    
    # With category and sender
    label_name = manager.get_newsletter_label_name(
        category='Tech',
        sender_name='Python Weekly'
    )
    assert label_name == 'Newsletters/Tech/Python-Weekly'


def test_clean_label_name():
    """Test label name cleaning."""
    mock_gog = Mock()
    manager = LabelManager(mock_gog)
    
    # Remove special characters
    assert manager._clean_label_name('Test@#$%Name') == 'TestName'
    
    # Replace spaces with hyphens
    assert manager._clean_label_name('Python Weekly') == 'Python-Weekly'
    
    # Trim long names
    long_name = 'A' * 100
    cleaned = manager._clean_label_name(long_name)
    assert len(cleaned) <= 50


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
