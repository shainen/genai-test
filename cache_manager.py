"""
Cache Manager for PDF Parsing

Provides caching functionality to avoid re-parsing PDFs on every run.
Uses pickle for serialization and file modification time to detect changes.
"""

import pickle
import os
import hashlib
from typing import List, Optional, Tuple
from pathlib import Path
from pdf_parsers import TextChunk, TableData


class CacheManager:
    """Manages caching of parsed PDF data"""

    def __init__(self, cache_dir: str = ".cache"):
        """
        Initialize cache manager.

        Args:
            cache_dir: Directory to store cache files
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

    def _get_cache_key(self, pdfs_folder: str) -> str:
        """
        Generate a cache key based on folder path and PDF file states.

        Args:
            pdfs_folder: Path to folder containing PDFs

        Returns:
            Hash string representing the current state of all PDFs
        """
        folder_path = Path(pdfs_folder)
        pdf_files = sorted(folder_path.glob("*.pdf"))

        # Create a hash based on:
        # 1. PDF file names
        # 2. File modification times
        # 3. File sizes
        hash_input = []
        for pdf_file in pdf_files:
            stat = pdf_file.stat()
            hash_input.append(f"{pdf_file.name}:{stat.st_mtime}:{stat.st_size}")

        combined = "|".join(hash_input)
        return hashlib.md5(combined.encode()).hexdigest()

    def _get_cache_path(self, pdfs_folder: str) -> Path:
        """
        Get the cache file path for a given PDF folder.

        Args:
            pdfs_folder: Path to folder containing PDFs

        Returns:
            Path to cache file
        """
        cache_key = self._get_cache_key(pdfs_folder)
        # Use folder name + hash to make it human-readable
        folder_name = Path(pdfs_folder).name
        return self.cache_dir / f"{folder_name}_{cache_key}.pkl"

    def load(self, pdfs_folder: str) -> Optional[Tuple[List[TextChunk], List[TextChunk], List[TableData]]]:
        """
        Load cached parsed data if available and valid.

        Args:
            pdfs_folder: Path to folder containing PDFs

        Returns:
            Tuple of (rules_chunks, rate_chunks, tables) if cache hit, None if cache miss
        """
        cache_path = self._get_cache_path(pdfs_folder)

        if not cache_path.exists():
            print(f"[Cache] Miss - no cache found for {pdfs_folder}")
            return None

        try:
            with open(cache_path, 'rb') as f:
                data = pickle.load(f)
                print(f"[Cache] Hit - loaded from {cache_path.name}")
                return data
        except Exception as e:
            print(f"[Cache] Error loading cache: {e}")
            return None

    def save(
        self,
        pdfs_folder: str,
        rules_chunks: List[TextChunk],
        rate_chunks: List[TextChunk],
        tables: List[TableData]
    ) -> None:
        """
        Save parsed data to cache.

        Args:
            pdfs_folder: Path to folder containing PDFs
            rules_chunks: Parsed rule chunks
            rate_chunks: Parsed rate chunks
            tables: Parsed tables
        """
        cache_path = self._get_cache_path(pdfs_folder)

        try:
            with open(cache_path, 'wb') as f:
                pickle.dump((rules_chunks, rate_chunks, tables), f)
                print(f"[Cache] Saved to {cache_path.name}")
        except Exception as e:
            print(f"[Cache] Error saving cache: {e}")

    def clear(self, pdfs_folder: Optional[str] = None) -> None:
        """
        Clear cache files.

        Args:
            pdfs_folder: If specified, only clear cache for this folder.
                        If None, clear all cache files.
        """
        if pdfs_folder:
            cache_path = self._get_cache_path(pdfs_folder)
            if cache_path.exists():
                cache_path.unlink()
                print(f"[Cache] Cleared {cache_path.name}")
        else:
            for cache_file in self.cache_dir.glob("*.pkl"):
                cache_file.unlink()
            print(f"[Cache] Cleared all cache files")

    def info(self, pdfs_folder: Optional[str] = None) -> None:
        """
        Print cache information.

        Args:
            pdfs_folder: If specified, show info for this folder only.
                        If None, show info for all cached folders.
        """
        if pdfs_folder:
            cache_path = self._get_cache_path(pdfs_folder)
            if cache_path.exists():
                stat = cache_path.stat()
                size_mb = stat.st_size / (1024 * 1024)
                print(f"[Cache] {cache_path.name}: {size_mb:.2f} MB")
            else:
                print(f"[Cache] No cache for {pdfs_folder}")
        else:
            cache_files = list(self.cache_dir.glob("*.pkl"))
            if not cache_files:
                print("[Cache] No cache files found")
            else:
                total_size = 0
                for cache_file in cache_files:
                    stat = cache_file.stat()
                    size_mb = stat.st_size / (1024 * 1024)
                    total_size += size_mb
                    print(f"[Cache] {cache_file.name}: {size_mb:.2f} MB")
                print(f"[Cache] Total: {total_size:.2f} MB across {len(cache_files)} files")
