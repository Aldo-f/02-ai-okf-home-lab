"""TDD test for numeric-dir scan + fork exclusion."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "documentation_watcher"))
import watcher

def test_freellmapi_is_fork_excluded():
    # RED: is_fork_repo should detect upstream remote for freellmapi
    result = watcher.is_fork_repo(Path.home() / "dev" / "02-ai-freellmapi")
    assert result is True, "freellmapi must be detected as fork"

def test_letspeppol_is_fork_excluded():
    result = watcher.is_fork_repo(Path.home() / "dev" / "06-apps-letspeppol")
    assert result is True, "letspeppol must be detected as fork"

def test_neobrutalist_not_fork():
    result = watcher.is_fork_repo(Path.home() / "dev" / "06-apps-neo-brutalist-home")
    assert result is False, "neo-brutalist should not be a fork"
