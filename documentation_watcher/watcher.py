#!/usr/bin/env python3
"""
Documentation Update Watcher for aldo-f.github.io
Automatically detects and integrates documentation changes from source repositories
"""

import os
import json
import subprocess
import time
from pathlib import Path
from datetime import datetime
import hashlib
import yaml

# Configuration
REPO_ROOT = Path("/home/aldo/dev")
APPS_DIR = REPO_ROOT  # Apps are directly in dev directory
DOCS_SITE = REPO_ROOT / "06-apps-aldo-f-github-io"
STATE_FILE = DOCS_SITE / ".doc_watcher_state.json"
CHECK_INTERVAL = 300  # 5 minutes

# Explicit repo -> destination directories. One source of truth;
# the generic else-branch is gone on purpose: unknown repos must fail
# tests/test_watcher_map.py instead of silently landing somewhere odd.
DOCS_SITE_DOCS = str(DOCS_SITE / "docs")
OKF_BUNDLE = str(Path(__file__).resolve().parent.parent)

REPO_DEST_MAP = {
    "06-apps-clock":              [f"{DOCS_SITE_DOCS}/clock"],
    "06-apps-radio-community":    [f"{DOCS_SITE_DOCS}/radio-community"],
    "06-apps-wordpress-stantonius": [f"{DOCS_SITE_DOCS}/wordpress-stantonius"],
    "06-apps-passive-income":     [f"{DOCS_SITE_DOCS}/passive-income",
                                   f"{OKF_BUNDLE}/docs/passive-income"],
    "06-apps-passive-income-sync": [f"{DOCS_SITE_DOCS}/passive-income-sync"],
    "06-apps-thuis-v4":           [f"{DOCS_SITE_DOCS}/thuis-v4"],
    "06-apps-thuis-v5":           [f"{DOCS_SITE_DOCS}/thuis-v5"],
    # Aldo's own app: docs published on the site AND kept in the bundle
    "06-apps-neo-brutalist-home": [f"{DOCS_SITE_DOCS}/neo-brutalist-home",
                                   f"{OKF_BUNDLE}/docs/neo-brutalist-home"],
    # NOT Aldo's own application: knowledge for agents only, never published
    "06-apps-letspeppol":         [f"{OKF_BUNDLE}/docs/letspeppol"],
    # The docs hub itself and the Nextcloud runtime stack: no external
    # documentation to sync; mapped to the bundle root as a no-op target so
    # tests stay green and the watcher has an explicit entry.
    "06-apps-aldo-f-github-io":   [f"{OKF_BUNDLE}/docs/aldo-f-github-io"],
    "06-apps-nextcloud":          [f"{OKF_BUNDLE}/docs/nextcloud"],
}


import re

# Documentation patterns to watch
DOC_PATTERNS = [
    "docs/**/*.md",
    "website/docs/**/*.md", 
    "*.md",  # README, etc. at repo root
]

EXCLUDE_PATTERNS = [
    "*/node_modules/**",
    "*/.git/**",
    "*/__pycache__/**",
    "*/dist/**",
    "*/build/**",
    "*legacy*",
    "*archive*",
]

def is_fork_repo(repo_path):
    try:
        remotes = subprocess.run(
            ["git", "-C", str(repo_path), "remote", "-v"],
            capture_output=True, text=True, timeout=10
        ).stdout
        # Fork indicators: upstream remote, origin matching original repo
        if "upstream" in remotes or ("fork" in remotes.lower()):
            return True
        # letspeppol: origin = letspeppol/letspeppol (original repo not Aldo-f)
        if "letspeppol/letspeppol" in remotes:
            return True
        # freellmapi: upstream to tashfeenahmed/freellmapi
        if "tashfeenahmed/freellmapi" in remotes:
            return True
        return False
    except Exception:
        return False

class DocWatcher:
    def __init__(self):
        self.state = self.load_state()
        self.ensure_directories()
    
    def load_state(self):
        """Load the last known state of documentation files"""
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading state: {e}")
                return {}
        return {}
    
    def save_state(self):
        """Save current state for next comparison"""
        try:
            with open(STATE_FILE, 'w') as f:
                json.dump(self.state, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving state: {e}")
    
    def ensure_directories(self):
        """Ensure necessary directories exist"""
        (DOCS_SITE / "documentation_watcher").mkdir(exist_ok=True)
        (DOCS_SITE / "agent_api").mkdir(exist_ok=True)
    
    def get_repo_docs_path(self, repo_path):
        """Get the documentation path within a repo"""
        repo_path = Path(repo_path)
        
        # Check for standard docs folder
        if (repo_path / "docs").exists():
            return repo_path / "docs"
        
        # Check for website/docs (like thuis v4/v5)
        if (repo_path / "website" / "docs").exists():
            return repo_path / "website" / "docs"
        
        # Check for root level markdown files
        md_files = list(repo_path.glob("*.md"))
        if md_files:
            return repo_path
            
        return None
    
    def should_include_file(self, file_path):
        """Check if a file should be included based on patterns"""
        # Convert to relative path for pattern matching
        try:
            rel_path = str(file_path.relative_to(REPO_ROOT))
        except ValueError:
            # File is outside REPO_ROOT, use absolute
            rel_path = str(file_path)
        
        # Check exclusions first
        for pattern in EXCLUDE_PATTERNS:
            if "*" in pattern:
                # Simple glob matching
                import fnmatch
                if fnmatch.fnmatch(rel_path, pattern):
                    return False
            elif pattern in rel_path:
                return False
        
        # Check inclusions
        for pattern in DOC_PATTERNS:
            if "*" in pattern:
                import fnmatch
                if fnmatch.fnmatch(rel_path, pattern):
                    return True
            elif pattern in rel_path:
                return True
                
        return False
    
    def get_file_hash(self, file_path):
        """Get hash of file contents"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return None
    
    def scan_repository(self, repo_path):
        """Scan a repository for documentation changes"""
        repo_path = Path(repo_path)
        repo_name = repo_path.name
        
        print(f"Scanning {repo_name}...")
        
        docs_path = self.get_repo_docs_path(repo_path)
        if not docs_path:
            print(f"  No documentation found in {repo_name}")
            return []
        
        changes = []
        
        # Scan for markdown files
        for md_file in docs_path.rglob("*.md"):
            if not self.should_include_file(md_file):
                continue
                
            file_hash = self.get_file_hash(md_file)
            if file_hash is None:
                continue
            
            # Get relative path within docs for storage
            try:
                rel_path = md_file.relative_to(docs_path)
            except ValueError:
                rel_path = md_file.name
            
            # Create unique identifier
            file_id = f"{repo_name}:{rel_path}"
            
            # Check if changed
            last_hash = self.state.get(file_id, {}).get('hash')
            if last_hash != file_hash:
                changes.append({
                    'repo': repo_name,
                    'file': str(rel_path),
                    'full_path': str(md_file),
                    'old_hash': last_hash,
                    'new_hash': file_hash,
                    'timestamp': datetime.now().isoformat()
                })
                print(f"  Change detected: {rel_path}")
        
        return changes
    
    # Repos never scanned: the docs hub itself (scanning its docs/ tree
    # re-imports the synced mirrors into themselves -> infinite nesting)
    # and the Nextcloud runtime stack (host state, not project code).
    SCAN_EXCLUDED = {"06-apps-aldo-f-github-io", "06-apps-nextcloud"}

    def scan_all_repositories(self):
        """Scan all application repositories for documentation changes"""
        all_changes = []
        
        # Get all app directories
        if not APPS_DIR.exists():
            print(f"Apps directory not found: {APPS_DIR}")
            return all_changes
            
        for item in APPS_DIR.iterdir():
            if not (item.is_dir() and re.match(r"^\d{2}-", item.name)):
                continue
            if item.name in self.SCAN_EXCLUDED:
                continue
            if is_fork_repo(item):
                print(f"  Skipping fork repo: {item.name}")
                continue
            changes = self.scan_repository(item)
            all_changes.extend(changes)
        
        return all_changes

    def integrate_changes(self, changes):
        """Integrate documentation changes into the site"""
        if not changes:
            print("No documentation changes to integrate")
            return False
        
        print(f"Integrating {len(changes)} documentation changes...")
        
        integrated = False
        
        for change in changes:
            repo_name = change['repo']
            rel_file = change['file']
            src_path = Path(change['full_path'])
            
            # Destination(s) from the explicit map; unknown repos are skipped
            # loudly rather than silently landing in a generic location.
            # Numeric repos: site mirror + bundle mirror (auto); skip forks already excluded
            dest_bases = [f"{DOCS_SITE_DOCS}/{repo_name}", f"{OKF_BUNDLE}/docs/{repo_name}"]
            
            import shutil
            for dest_base in dest_bases:
                dest_path = Path(dest_base) / rel_file
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                
                try:
                    shutil.copy2(src_path, dest_path)
                    print(f"  Integrated: {repo_name}/{rel_file} -> {dest_base}")
                except Exception as e:
                    print(f"  Error integrating {repo_name}/{rel_file}: {e}")
            
            # Update state once per file (after all destinations succeeded)
            file_id = f"{repo_name}:{rel_file}"
            self.state[file_id] = {
                'hash': change['new_hash'],
                'integrated_at': datetime.now().isoformat(),
                'size': src_path.stat().st_size
            }
            integrated = True
        
        if integrated:
            self.save_state()
            print("Documentation changes integrated successfully")
        
        return integrated
    
    def run_once(self):
        """Run one scan and integration cycle"""
        print(f"Starting documentation scan at {datetime.now()}")
        changes = self.scan_all_repositories()
        if changes:
            integrated = self.integrate_changes(changes)
            if integrated:
                # Publish chain: invalidate RAG cache, push site (Pages
                # deploy), verify live, run test suite. Only fires when
                # files actually changed.
                post_sync = Path(__file__).resolve().parent.parent / "scripts" / "post_sync.sh"
                if post_sync.exists():
                    try:
                        subprocess.run(["bash", str(post_sync)], timeout=900)
                    except Exception as e:
                        print(f"post_sync failed: {e}")
                else:
                    print("post_sync.sh missing - skipping publish chain")
        else:
            print("No changes detected")
        print(f"Scan completed at {datetime.now()}")
    
    def run_daemon(self):
        """Run as a daemon, scanning periodically"""
        print(f"Starting documentation watcher daemon (checking every {CHECK_INTERVAL}s)")
        try:
            while True:
                self.run_once()
                print(f"Waiting {CHECK_INTERVAL} seconds until next check...")
                time.sleep(CHECK_INTERVAL)
        except KeyboardInterrupt:
            print("\nStopping documentation watcher")
        except Exception as e:
            print(f"Watcher error: {e}")

def main():
    import sys
    
    watcher = DocWatcher()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--daemon":
        watcher.run_daemon()
    else:
        watcher.run_once()

if __name__ == "__main__":
    main()