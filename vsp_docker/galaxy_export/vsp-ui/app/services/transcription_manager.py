"""
Unified Transcription Manager

Manages all transcriptions (manual and auto-generated) in a persistent storage
location that survives pipeline runs. Provides CRUD operations, metadata tracking,
and orphan detection.
"""

from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import json


@dataclass
class TranscriptionInfo:
    """Information about a transcription."""
    filename: str
    type: str  # "auto" or "manual"
    created_at: str
    edited_at: Optional[str]
    word_count: int
    video_checksum: Optional[str]
    is_orphaned: bool  # True if video not in input folder


def _get_transcriptions_dir() -> Path:
    """
    Get transcriptions directory from config INPUT_DIR.

    Returns:
        Path to .transcriptions directory based on INPUT_DIR
    """
    from app.config import INPUT_DIR
    return INPUT_DIR / ".transcriptions"


class TranscriptionManager:
    """Manages unified transcription storage for both manual and auto transcriptions."""

    TRANSCRIPTIONS_DIR = _get_transcriptions_dir()
    METADATA_FILE = TRANSCRIPTIONS_DIR / "metadata.json"

    def __init__(self):
        """Initialize the transcription manager."""
        self.TRANSCRIPTIONS_DIR.mkdir(parents=True, exist_ok=True)
        self._load_metadata()

    # === Core CRUD Operations ===

    def save_transcription(
        self,
        filename: str,
        text: str,
        transcription_type: str = "manual"
    ) -> Dict:
        """
        Save transcription with normalized text.

        Args:
            filename: Video filename (e.g., "video1.mp4")
            text: Transcription text (space or newline separated words)
            transcription_type: "manual" or "auto"

        Returns:
            Dict with success status and word count
        """
        # Normalize text (one word per line)
        words = self.normalize_text(text)

        # Write .wrd file
        stem = Path(filename).stem
        wrd_path = self.TRANSCRIPTIONS_DIR / f"{stem}.wrd"
        wrd_path.write_text("\n".join(words))

        # Update metadata
        now = datetime.utcnow().isoformat() + "Z"
        existing = self.metadata["transcriptions"].get(filename, {})

        self.metadata["transcriptions"][filename] = {
            "type": transcription_type,
            "created_at": existing.get("created_at", now),
            "edited_at": now if existing else None,
            "word_count": len(words),
            "video_checksum": existing.get("video_checksum"),
        }

        self._save_metadata()

        return {"success": True, "word_count": len(words)}

    def get_transcription(self, filename: str) -> Optional[str]:
        """
        Get transcription text (space-joined for display).

        Args:
            filename: Video filename

        Returns:
            Space-separated transcription text, or None if not found
        """
        stem = Path(filename).stem
        wrd_path = self.TRANSCRIPTIONS_DIR / f"{stem}.wrd"

        if not wrd_path.exists():
            return None

        words = wrd_path.read_text().strip().split("\n")
        return " ".join(words)

    def delete_transcription(self, filename: str) -> bool:
        """
        Delete transcription file and metadata.

        Args:
            filename: Video filename

        Returns:
            True if deleted, False if not found
        """
        stem = Path(filename).stem
        wrd_path = self.TRANSCRIPTIONS_DIR / f"{stem}.wrd"

        if wrd_path.exists():
            wrd_path.unlink()

        if filename in self.metadata["transcriptions"]:
            del self.metadata["transcriptions"][filename]
            self._save_metadata()
            return True

        return False

    def has_transcription(self, filename: str) -> bool:
        """
        Check if transcription exists.

        Args:
            filename: Video filename

        Returns:
            True if transcription exists
        """
        stem = Path(filename).stem
        wrd_path = self.TRANSCRIPTIONS_DIR / f"{stem}.wrd"
        return wrd_path.exists()

    def get_transcription_info(self, filename: str) -> Optional[TranscriptionInfo]:
        """
        Get full metadata for a transcription.

        Args:
            filename: Video filename

        Returns:
            TranscriptionInfo object, or None if not found
        """
        if not self.has_transcription(filename):
            return None

        meta = self.metadata["transcriptions"].get(filename, {})
        stem = Path(filename).stem
        wrd_path = self.TRANSCRIPTIONS_DIR / f"{stem}.wrd"
        word_count = len(wrd_path.read_text().strip().split("\n"))

        return TranscriptionInfo(
            filename=filename,
            type=meta.get("type", "manual"),
            created_at=meta.get("created_at"),  # Returns None if not present
            edited_at=meta.get("edited_at"),
            word_count=word_count,
            video_checksum=meta.get("video_checksum"),
            is_orphaned=False,  # Set by caller
        )

    # === Orphan Management ===

    def get_orphaned_transcriptions(
        self,
        valid_filenames: List[str]
    ) -> List[TranscriptionInfo]:
        """
        Find transcriptions without corresponding videos.

        Args:
            valid_filenames: List of valid video filenames in input folder

        Returns:
            List of TranscriptionInfo for orphaned transcriptions
        """
        valid_stems = {Path(f).stem for f in valid_filenames}
        orphaned = []

        for wrd_file in self.TRANSCRIPTIONS_DIR.glob("*.wrd"):
            stem = wrd_file.stem

            # Check if any valid filename matches this stem
            if stem not in valid_stems:
                # Reconstruct likely filename (assume .mp4)
                filename = f"{stem}.mp4"

                # Try to get metadata
                meta = self.metadata["transcriptions"].get(filename, {})

                info = TranscriptionInfo(
                    filename=filename,
                    type=meta.get("type", "auto"),
                    created_at=meta.get("created_at", ""),
                    edited_at=meta.get("edited_at"),
                    word_count=len(wrd_file.read_text().strip().split("\n")),
                    video_checksum=meta.get("video_checksum"),
                    is_orphaned=True,
                )
                orphaned.append(info)

        return orphaned

    # === Whisper Integration ===

    def save_whisper_output(
        self,
        wrd_source_path: Path,
        video_filename: str
    ) -> bool:
        """
        Copy Whisper .wrd output to .transcriptions/ as 'auto' type.

        Args:
            wrd_source_path: Path to source .wrd file from Whisper
            video_filename: Original video filename

        Returns:
            True if saved successfully
        """
        if not wrd_source_path.exists():
            return False

        # Copy file
        dest_path = self.TRANSCRIPTIONS_DIR / wrd_source_path.name
        dest_path.write_text(wrd_source_path.read_text())

        # Update metadata
        word_count = len(wrd_source_path.read_text().strip().split("\n"))
        now = datetime.utcnow().isoformat() + "Z"

        self.metadata["transcriptions"][video_filename] = {
            "type": "auto",
            "created_at": now,
            "edited_at": None,
            "word_count": word_count,
            "video_checksum": None,  # TODO: compute hash for change detection
        }

        self._save_metadata()
        return True

    # === Utility Methods ===

    def normalize_text(self, text: str) -> List[str]:
        """
        Normalize text to match ASR tokenization.

        Args:
            text: Input text (space or newline separated)

        Returns:
            List of normalized words (lowercase, alphanumeric + apostrophes)
        """
        # Split on whitespace
        words = text.lower().split()

        # Keep only alphanumeric + apostrophes
        normalized = []
        for word in words:
            cleaned = ''.join(c for c in word if c.isalnum() or c == "'")
            if cleaned:
                normalized.append(cleaned)

        return normalized

    def _load_metadata(self):
        """Load metadata.json from disk."""
        if self.METADATA_FILE.exists():
            self.metadata = json.loads(self.METADATA_FILE.read_text())
        else:
            self.metadata = {"transcriptions": {}}

    def _save_metadata(self):
        """Save metadata.json to disk."""
        self.METADATA_FILE.write_text(json.dumps(self.metadata, indent=2))
