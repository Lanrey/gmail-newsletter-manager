# Gmail Newsletter Manager - Project Structure

```
gmail-newsletter-manager/
├── src/
│   └── newsletter_manager/
│       ├── __init__.py           # Package initialization
│       ├── cli.py                 # Main CLI interface with all commands
│       ├── config.py              # Configuration management
│       ├── database.py            # SQLite database management
│       ├── gogcli_wrapper.py      # Python wrapper for gogcli commands
│       ├── newsletter_detector.py # Newsletter detection logic
│       └── label_manager.py       # Gmail label management
│
├── tests/
│   ├── __init__.py
│   ├── test_newsletter_detector.py  # Tests for newsletter detection
│   └── test_label_manager.py        # Tests for label management
│
├── docs/
│   ├── SETUP.md                  # Detailed setup guide
│   ├── EXAMPLES.md               # Usage examples
│   └── ARCHITECTURE.md           # This file
│
├── pyproject.toml                # Project configuration and dependencies
├── README.md                     # Project overview
├── LICENSE                       # MIT License
├── .gitignore                    # Git ignore rules
└── setup.sh                      # Quick setup script

Configuration & Data (created at runtime):
~/.gmail-newsletter-manager/
├── config.yaml                   # User configuration
└── newsletters.db                # SQLite database
```

## Architecture

### Core Components

#### 1. CLI Interface (`cli.py`)
- Built with argparse (Python stdlib)
- Rich terminal output (tables, colors, progress bars)
- Commands: discover, list, organize, cleanup, report, export, etc.
- Handles user interaction and error display

#### 2. Configuration Management (`config.py`)
- Loads/saves YAML configuration
- Default configuration with sensible defaults
- Category definitions for auto-categorization
- Newsletter detection patterns and platforms
- User customizable settings

#### 3. Database Layer (`database.py`)
- SQLite for local data storage
- Tables:
  - `newsletters`: Newsletter metadata, sender info, categories
  - `messages`: Individual message tracking
  - `scan_history`: Scan operation history
  - `operations_log`: Operation history for potential undo
- Efficient indexing for fast queries
- CRUD operations for all entities

#### 4. gogcli Wrapper (`gogcli_wrapper.py`)
- Python interface to gogcli CLI
- JSON output parsing
- Command error handling
- Methods for:
  - Searching messages
  - Getting message details
  - Label management (create, list, apply)
  - Batch operations
  - Message modification (archive, trash, mark read)

#### 5. Newsletter Detection (`newsletter_detector.py`)
- Heuristic-based newsletter identification:
  - List-Unsubscribe header (strongest indicator)
  - Known platform domains (Substack, Mailchimp, etc.)
  - Subject line patterns
  - Bulk sender patterns
  - Message content analysis
- Frequency analysis for sender patterns
- Auto-categorization based on keywords and domains
- Unsubscribe link extraction

#### 6. Label Management (`label_manager.py`)
- Gmail label operations via gogcli
- Hierarchical label creation (Newsletters/Category/Sender)
- Label caching for performance
- Batch label application
- Label name sanitization

## Data Flow

### Discovery Flow
```
User runs: newsletter-manager discover
    ↓
CLI → gogcli_wrapper.search_messages()
    ↓
gogcli → Gmail API (returns messages)
    ↓
For each message:
    newsletter_detector.is_newsletter()
    newsletter_detector.categorize_newsletter()
    database.upsert_newsletter()
    database.add_message()
    ↓
Display progress and results
```

### Organization Flow
```
User runs: newsletter-manager organize
    ↓
CLI → database.get_all_newsletters()
    ↓
For each newsletter:
    label_manager.create_label_hierarchy()
    label_manager.apply_label_to_messages()
    ↓
Display results
```

### Report Flow
```
User runs: newsletter-manager report
    ↓
CLI → database.get_all_newsletters()
    ↓
Aggregate statistics
Calculate engagement metrics
Format with Rich tables
    ↓
Display report
```

## Key Design Decisions

### 1. Local-First Architecture
- All processing happens locally
- SQLite database for caching and tracking
- Privacy-focused: no data sent to external services
- Fast repeated operations (no need to refetch from Gmail)

### 2. gogcli Integration
- Leverages existing, well-maintained CLI tool
- No need to implement OAuth/API client
- JSON output for easy parsing
- Handles rate limiting and authentication

### 3. Heuristic Detection
- Multiple indicators for robust newsletter detection
- Weighted scoring system
- Configurable patterns and thresholds
- Can handle various newsletter formats and platforms

### 4. Incremental Processing
- Scan history tracking
- Efficient delta updates
- Batch operations for performance
- Progress indicators for long operations

### 5. User Configurability
- YAML configuration for easy editing
- Custom categories and keywords
- Adjustable detection sensitivity
- Dry-run mode for safety

## Extension Points

### Adding New Commands
Add a new command method to the NewsletterCLI class in `cli.py`:

```python
def cmd_your_command(self, args):
    """Your command description."""
    # Implementation

# Then add the parser in main():
parser_your_cmd = subparsers.add_parser('your-command', help='Description')
parser_your_cmd.add_argument('--your-option', help='Option description')
```

### Adding New Categories
Edit `~/.gmail-newsletter-manager/config.yaml`:

```yaml
categories:
  YourCategory:
    keywords: [keyword1, keyword2]
    domains: [domain1.com, domain2.com]
```

### Custom Detection Rules
Extend `NewsletterDetector.is_newsletter()` in `newsletter_detector.py` to add custom detection logic.

### Database Schema Changes
1. Update table creation in `database.py`
2. Add migration logic if needed
3. Update CRUD methods

## Performance Considerations

### Caching
- Labels cached in memory after first fetch
- Database stores message metadata (no need to refetch)
- Configuration loaded once per command

### Batch Operations
- `batch_modify_messages()` for bulk label changes
- Configurable batch sizes
- Progress indicators for user feedback

### Rate Limiting
- Gmail API has rate limits (user: 250 quota units/second)
- gogcli handles basic rate limiting
- User can control scan size with `--max-results` and `--days`

### Database Indexes
- Indexed on common query patterns:
  - sender_email, category (newsletters table)
  - newsletter_id, received_date (messages table)

## Security & Privacy

### Authentication
- Uses gogcli's OAuth2 implementation
- Tokens stored securely by gogcli (OS keychain or encrypted file)
- No passwords stored by newsletter-manager

### Data Storage
- All data stored locally in SQLite
- No external API calls except to Gmail via gogcli
- Configuration file is plain text (no secrets)

### Permissions
- Minimal Gmail API scopes required:
  - `gmail.readonly` for reading messages
  - `gmail.modify` for label changes
  - `gmail.labels` for label management

## Testing

### Unit Tests
- `test_newsletter_detector.py`: Detection logic tests
- `test_label_manager.py`: Label management tests
- Uses pytest framework
- Mock gogcli responses for isolation

### Running Tests
```bash
source venv/bin/activate
pip install pytest
pytest tests/ -v
```

## Future Enhancements

### Planned Features
1. **Filter Creation**: Auto-create Gmail filters for new newsletters
2. **Analytics Dashboard**: Web-based visualization
3. **ML Categorization**: Machine learning for better auto-categorization
4. **Bulk Unsubscribe**: Automated unsubscribe via API or links
5. **Digest Mode**: Generate newsletter digests
6. **Integration**: Read-it-later services (Pocket, Instapaper)
7. **Cross-device Sync**: Cloud sync for preferences

### Plugin System
Future: Allow custom plugins for:
- Detection rules
- Categorization logic
- Export formats
- Custom commands

## Dependencies

### Required
- Python 3.8+
- gogcli (external binary)
- argparse (CLI framework - Python stdlib)
- rich (terminal output)
- pyyaml (configuration parsing)
- requests (HTTP client)

### Optional (Development)
- pytest (testing)
- black (code formatting)
- ruff (linting)

## Maintenance

### Updating Dependencies
```bash
pip install --upgrade -r requirements.txt
```

### Database Migrations
Currently: Manual (backup and recreate)
Future: Implement migration system (e.g., Alembic)

### Backup
```bash
# Backup database
cp ~/.gmail-newsletter-manager/newsletters.db ~/backup/

# Backup config
cp ~/.gmail-newsletter-manager/config.yaml ~/backup/
```
