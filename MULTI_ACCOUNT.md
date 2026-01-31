# Multi-Account Support

The newsletter manager now supports managing multiple Gmail accounts. You can:
- Add multiple accounts
- Set a default account
- Run commands against a specific account

## Commands

### View all accounts
```bash
newsletter-manager account list
```

### Add an account
```bash
newsletter-manager account add user@gmail.com
```
The first account added automatically becomes the default.

### Set default account
When you don't specify `--account`, the default is used:
```bash
newsletter-manager account set-default another@gmail.com
```

### Remove an account
```bash
newsletter-manager account remove user@gmail.com --force
```
(Use `--force` to skip confirmation)

## Using with Commands

### Run with default account
```bash
newsletter-manager discover
newsletter-manager list
newsletter-manager apply-labels
```

### Run with specific account
```bash
newsletter-manager --account another@gmail.com discover
newsletter-manager --account another@gmail.com apply-labels
newsletter-manager --account user1@gmail.com migrate-labels
```

### Environment variable
You can also set the account via `GOG_ACCOUNT`:
```bash
export GOG_ACCOUNT=another@gmail.com
newsletter-manager discover
```

## Account Storage

Accounts are stored in `~/.gmail-newsletter-manager/config.yaml`:
```yaml
accounts:
  - user1@gmail.com
  - user2@gmail.com
  - user3@gmail.com
default_account: user1@gmail.com
```

Each account uses its own gog CLI credentials (managed by `gog config` separately for each account).
