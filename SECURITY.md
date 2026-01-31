# Security Policy

## Supported Versions

We release patches for security vulnerabilities for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability within Gmail Newsletter Manager, please send an email to olusolaakinsulere@gmail.com. All security vulnerabilities will be promptly addressed.

Please include the following information:

1. **Description of the vulnerability**
2. **Steps to reproduce**
3. **Potential impact**
4. **Suggested fix** (if any)

### What to expect

- **Response time**: You can expect an initial response within 48 hours
- **Updates**: We will keep you informed about the progress of the fix
- **Credit**: If you wish, we will credit you in the release notes

## Security Best Practices

When using Gmail Newsletter Manager:

### 1. Protect Your Credentials

- **Never commit** OAuth credentials or tokens to version control
- Store OAuth credentials securely using the built-in credential management:
  ```bash
  gog auth credentials set /path/to/credentials.json
  ```
- Use environment variables for sensitive configuration when possible

### 2. Configuration Files

- The default configuration is stored at `~/.gmail-newsletter-manager/config.yaml`
- This file is automatically excluded from version control via `.gitignore`
- **Never share** your `config.yaml` file publicly

### 3. Database Security

- The SQLite database (`newsletters.db`) is stored locally
- Ensure the database directory has proper permissions (read/write for owner only)
- Regular backups are recommended but keep backups secure

### 4. API Tokens

- OAuth tokens are managed by `gogcli` and stored in `~/.ogg/credentials`
- Tokens are automatically refreshed by gogcli
- If you suspect token compromise, revoke access via [Google Account Settings](https://myaccount.google.com/permissions)

### 5. Multi-Account Security

When using multiple accounts:

- Use separate OAuth credentials for each account when possible
- Be explicit with `--account` flag to avoid accidental operations on wrong account
- Review account list regularly: `newsletter-manager account list`

### 6. Rate Limiting

- The application implements rate limiting to prevent API abuse
- Don't disable or reduce rate limiting without understanding the implications
- Excessive API calls may trigger Google's abuse detection

### 7. Third-Party Dependencies

- We regularly update dependencies to patch security vulnerabilities
- Run `pip install --upgrade gmail-newsletter-manager` to get latest security updates
- Monitor security advisories for Python and our dependencies

## Known Limitations

1. **OAuth Scope**: This application requires Gmail API access. Review permissions carefully
2. **Local Storage**: Data is stored unencrypted locally. Ensure your system is secure
3. **API Rate Limits**: Google enforces rate limits. Application respects these but may be delayed

## Security Features

### What We Do

✅ Use OAuth 2.0 for authentication (no password storage)
✅ Rate limiting to prevent API abuse
✅ Input validation on user-provided data
✅ Exclude sensitive files from version control
✅ Clear documentation on secure configuration

### What We Don't Do

❌ Store passwords or API keys in code
❌ Transmit credentials over insecure channels
❌ Share user data with third parties
❌ Log sensitive information

## Compliance

This application:
- Uses Google's official OAuth 2.0 flow
- Complies with Google's API Terms of Service
- Stores data locally only (no cloud storage)
- Does not track or analyze user behavior

## Questions?

If you have security-related questions that don't constitute a vulnerability report, please open a GitHub issue with the `security` label or email olusolaakinsulere@gmail.com.
