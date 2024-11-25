import os
import json
import hashlib
from pathlib import Path
from typing import Optional, Dict, Tuple


class ModernMetricCache:
    """Cache class for ModernMetric scan"""

    def __init__(self, cache_dir: str = ".modernmetric_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def calculate_file_hash(self, file_path: str) -> str:
        """generate hash based on file content and modification time"""
        file_path = Path(file_path)
        if not file_path.exists():
            return ""

        mtime = str(os.path.getmtime(file_path))

        with open(file_path, 'rb') as f:
            content = f.read()

        # Combine content and mtime for the hash
        hash_content = content + mtime.encode('utf-8')
        return hashlib.sha256(hash_content).hexdigest()

    def get_cache_path(self, file_hash: str) -> Path:
        """Get path to cached result file"""
        return self.cache_dir / f"{file_hash}.json"

    def get_cached_result(
        self, file_path: str
    ) -> Optional[Tuple[Dict, str, str, list, Dict]]:
        """
        Retrieve cached results if they exist and are valid
        Returns: (res, file_path, lexer_name, tokens, store) or None
        """
        file_hash = self.calculate_file_hash(file_path)
        cache_path = self.get_cache_path(file_hash)

        if not cache_path.exists():
            return None

        try:
            with open(cache_path, 'r') as f:
                cached_data = json.load(f)
                return (
                    cached_data['res'],
                    cached_data['file'],
                    cached_data['lexer_name'],
                    cached_data['tokens'],
                    cached_data['store']
                )
        except (json.JSONDecodeError, KeyError):
            cache_path.unlink(missing_ok=True)
            return None

    def store_result(
        self,
        file_path: str,
        result: Tuple[Dict, str, str, list, Dict]
    ) -> None:
        """Store scan results in cache"""
        file_hash = self.calculate_file_hash(file_path)
        cache_path = self.get_cache_path(file_hash)

        cache_data = {
            'res': result[0],
            'file': result[1],
            'lexer_name': result[2],
            'tokens': result[3],
            'store': result[4]
        }

        with open(cache_path, 'w') as f:
            json.dump(cache_data, f)
