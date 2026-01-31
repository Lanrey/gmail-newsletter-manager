"""Python wrapper for gogcli commands."""

import json
import subprocess
from typing import Dict, List, Optional, Any
import os
import time


class GogCLIError(Exception):
    """Exception raised when gogcli command fails."""
    pass


class GogCLI:
    """Wrapper for gogcli commands."""
    
    def __init__(self, account: Optional[str] = None):
        """Initialize gogcli wrapper.
        
        Args:
            account: Gmail account to use. If None, uses GOG_ACCOUNT env var or default.
        """
        self.account = account or os.getenv('GOG_ACCOUNT')
        self._check_gogcli_installed()
    
    def _check_gogcli_installed(self) -> None:
        """Check if gogcli is installed."""
        try:
            subprocess.run(['gog', '--version'], capture_output=True, check=True)
        except FileNotFoundError:
            raise GogCLIError(
                "gogcli is not installed. Install it with: brew install steipete/tap/gogcli"
            )
        except subprocess.CalledProcessError:
            pass  # Command might not support --version, but gog exists
    
    def _run_command(self, args: List[str], json_output: bool = True) -> Any:
        """Run a gogcli command and return output.
        
        Args:
            args: Command arguments (without 'gog' prefix)
            json_output: Whether to parse JSON output
            
        Returns:
            Parsed JSON output or raw string
        """
        cmd = ['gog']
        
        if self.account:
            cmd.extend(['--account', self.account])
        
        if json_output:
            cmd.append('--json')
        
        cmd.extend(args)
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            if json_output and result.stdout:
                return json.loads(result.stdout)
            return result.stdout
        
        except subprocess.CalledProcessError as e:
            raise GogCLIError(f"Command failed: {' '.join(cmd)}\nError: {e.stderr}")
        except json.JSONDecodeError as e:
            raise GogCLIError(f"Failed to parse JSON output: {e}\nOutput: {result.stdout}")
    
    def search_messages(self, query: str, max_results: Optional[int] = None, 
                       page_token: Optional[str] = None) -> Dict:
        """Search Gmail messages with pagination support.
        
        Args:
            query: Gmail search query
            max_results: Maximum number of results per page
            page_token: Page token for pagination
            
        Returns:
            Dict with 'threads' and optional 'nextPageToken'
        """
        args = ['gmail', 'search', query]
        if max_results:
            args.extend(['--max', str(max_results)])
        if page_token:
            args.extend(['--page', page_token])
        
        result = self._run_command(args)
        
        # gog returns {threads: [...], nextPageToken: ...} structure
        if isinstance(result, dict):
            return result
        elif isinstance(result, list):
            return {'threads': result}
        return {'threads': []}
    
    def search_all_messages(self, query: str, max_total: Optional[int] = None,
                           page_size: int = 500, progress_callback=None, 
                           rate_limit_delay: float = 5.0) -> List[Dict]:
        """Search all Gmail messages with automatic pagination and rate limiting.
        
        Args:
            query: Gmail search query
            max_total: Maximum total results to return (None = unlimited)
            page_size: Results per page (max 500)
            progress_callback: Optional callback function(page_num, total_so_far)
            rate_limit_delay: Delay in seconds between API calls to avoid rate limits
            
        Returns:
            List of all message/thread dictionaries
        """
        all_threads = []
        page_token = None
        page_count = 0
        max_retries = 5
        consecutive_failures = 0
        
        while True:
            page_count += 1
            if progress_callback:
                progress_callback(page_count, len(all_threads))
            
            # Adaptive rate limiting - increase delay after failures
            current_delay = rate_limit_delay * (1 + consecutive_failures)
            if page_count > 1:
                # Extra delay every 10 pages to be safe
                delay = current_delay * (2 if page_count % 10 == 0 else 1)
                time.sleep(delay)
            
            # Retry logic for rate limit errors
            retry_count = 0
            for retry in range(max_retries):
                try:
                    result = self.search_messages(query, max_results=page_size, page_token=page_token)
                    consecutive_failures = 0  # Reset on success
                    break
                except GogCLIError as e:
                    error_str = str(e)
                    if 'rateLimitExceeded' in error_str or '429' in error_str or '403' in error_str:
                        retry_count = retry + 1
                        if retry < max_retries - 1:
                            wait_time = (retry + 2) * 20  # Exponential backoff: 20s, 40s, 60s, 80s, 100s
                            if progress_callback:
                                progress_callback(f"⏱️ Rate limited, waiting {wait_time}s (retry {retry_count}/{max_retries})", len(all_threads))
                            time.sleep(wait_time)
                            consecutive_failures += 1
                            continue
                        else:
                            # Max retries reached
                            consecutive_failures += 1
                            if progress_callback:
                                progress_callback(f"⚠️ Max retries reached after {len(all_threads)} messages", len(all_threads))
                    raise
            
            threads = result.get('threads', [])
            
            if not threads:
                break
            
            all_threads.extend(threads)
            
            # Check if we've reached the max total
            if max_total and len(all_threads) >= max_total:
                all_threads = all_threads[:max_total]
                break
            
            # Check for next page
            page_token = result.get('nextPageToken')
            if not page_token:
                break
        
        return all_threads
    
    def get_message(self, message_id: str, format: str = 'full') -> Dict:
        """Get a specific message.
        
        Args:
            message_id: Message ID
            format: Message format (full, metadata, minimal)
            
        Returns:
            Message dictionary
        """
        args = ['gmail', 'messages', 'get', message_id, '--format', format]
        return self._run_command(args)
    
    def list_labels(self) -> List[Dict]:
        """List all Gmail labels.
        
        Returns:
            List of label dictionaries
        """
        result = self._run_command(['gmail', 'labels', 'list'])
        if isinstance(result, dict):
            return result.get('labels', [])
        return result if isinstance(result, list) else []
    
    def create_label(self, name: str, label_list_visibility: str = 'labelShow',
                    message_list_visibility: str = 'show') -> Dict:
        """Create a Gmail label.
        
        Args:
            name: Label name (use / for hierarchy, e.g., "Newsletters/Tech")
            label_list_visibility: Visibility in label list
            message_list_visibility: Visibility in message list
            
        Returns:
            Created label dictionary
        """
        args = ['gmail', 'labels', 'create', name]
        return self._run_command(args)
    
    def modify_message_labels(self, message_id: str, add_labels: Optional[List[str]] = None,
                             remove_labels: Optional[List[str]] = None) -> Dict:
        """Modify labels on a message.
        
        Args:
            message_id: Message ID
            add_labels: Labels to add
            remove_labels: Labels to remove
            
        Returns:
            Modified message dictionary
        """
        args = ['gmail', 'messages', 'modify', message_id]
        
        if add_labels:
            for label in add_labels:
                args.extend(['--add-label', label])
        
        if remove_labels:
            for label in remove_labels:
                args.extend(['--remove-label', label])
        
        return self._run_command(args)

    def modify_thread_labels(self, thread_id: str, add_labels: Optional[List[str]] = None,
                            remove_labels: Optional[List[str]] = None) -> None:
        """Modify labels on all messages in a thread.
        
        Args:
            thread_id: Thread ID
            add_labels: Labels to add (names or IDs)
            remove_labels: Labels to remove (names or IDs)
        """
        args = ['gmail', 'thread', 'modify', thread_id]

        if add_labels:
            args.extend(['--add', ','.join(add_labels)])

        if remove_labels:
            args.extend(['--remove', ','.join(remove_labels)])

        self._run_command(args, json_output=False)
    
    def batch_modify_messages(self, message_ids: List[str], add_labels: Optional[List[str]] = None,
                             remove_labels: Optional[List[str]] = None) -> None:
        """Batch modify labels on multiple messages.
        
        Args:
            message_ids: List of message IDs
            add_labels: Labels to add
            remove_labels: Labels to remove
        """
        # gog gmail batch modify <messageId> ... --add=labels --remove=labels
        args = ['gmail', 'batch', 'modify']
        
        # Add all message IDs as arguments
        args.extend(message_ids)
        
        if add_labels:
            args.extend(['--add', ','.join(add_labels)])
        
        if remove_labels:
            args.extend(['--remove', ','.join(remove_labels)])
        
        self._run_command(args, json_output=False)
    
    def trash_message(self, message_id: str) -> None:
        """Move message to trash.
        
        Args:
            message_id: Message ID
        """
        self._run_command(['gmail', 'messages', 'trash', message_id], json_output=False)
    
    def archive_message(self, message_id: str) -> None:
        """Archive a message (remove from INBOX).
        
        Args:
            message_id: Message ID
        """
        self.modify_message_labels(message_id, remove_labels=['INBOX'])
    
    def mark_as_read(self, message_id: str) -> None:
        """Mark message as read.
        
        Args:
            message_id: Message ID
        """
        self.modify_message_labels(message_id, remove_labels=['UNREAD'])
    
    def mark_as_unread(self, message_id: str) -> None:
        """Mark message as unread.
        
        Args:
            message_id: Message ID
        """
        self.modify_message_labels(message_id, add_labels=['UNREAD'])
    
    def create_filter(self, criteria: Dict[str, str], action: Dict[str, Any]) -> Dict:
        """Create a Gmail filter.
        
        Args:
            criteria: Filter criteria (e.g., {"from": "newsletter@example.com"})
            action: Filter action (e.g., {"addLabelIds": ["Label_123"]})
            
        Returns:
            Created filter dictionary
        """
        # Note: gogcli may not support filter creation directly
        # This is a placeholder for the API structure
        raise NotImplementedError("Filter creation via gogcli needs to be verified")
    
    def get_account_info(self) -> Dict:
        """Get current account information.
        
        Returns:
            Account info dictionary
        """
        return self._run_command(['auth', 'status'])
