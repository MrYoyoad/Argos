"""
Pipeline runner with subprocess management and watchdog.
Handles execution, monitoring, cancellation, and error recovery.
"""
import os
import signal
import subprocess
import threading
import time
import shutil
from pathlib import Path
from typing import Optional, Callable, List
from datetime import datetime

from ..config import (
    INPUT_DIR,
    PIPELINE_SCRIPT,
    ARCHIVE_DIR,
    AUTO_AVSR_DIR,
    PipelineState,
)
from .progress_tracker import ProgressTracker


class PipelineRunner:
    """Manages pipeline subprocess execution with watchdog monitoring."""

    def __init__(self):
        self.tracker = ProgressTracker()
        self.process: Optional[subprocess.Popen] = None
        self._cancel_requested = False
        self._lock = threading.Lock()
        self._monitor_thread: Optional[threading.Thread] = None
        self._on_progress: Optional[Callable] = None
        self._run_id: Optional[str] = None
        self._train_kmeans: bool = True
        self._golden_model: Optional[str] = None

    @property
    def is_running(self) -> bool:
        """Check if pipeline is currently running."""
        with self._lock:
            return self.process is not None and self.process.poll() is None

    @property
    def state(self) -> str:
        """Get current pipeline state."""
        return self.tracker.state.state

    def get_progress(self) -> dict:
        """Get current progress state as dictionary."""
        return self.tracker.state.to_dict()

    def get_logs(self, n: int = 50) -> List[str]:
        """Get recent log lines."""
        return self.tracker.get_recent_logs(n)

    def get_all_logs(self) -> str:
        """Get all logs as string."""
        return self.tracker.get_all_logs()

    def start(
        self,
        on_progress: Optional[Callable] = None,
        train_kmeans: bool = True,
        golden_model: Optional[str] = None,
        segmentation_enabled: bool = True,
        overlap_enabled: bool = True,
        segment_only: bool = True,
    ) -> bool:
        """
        Start the pipeline execution.

        Args:
            on_progress: Callback function called on progress updates
            train_kmeans: Whether to train k-means model (default True)
            golden_model: Path to golden k-means model to use (default None)
            segmentation_enabled: Whether to enable video segmentation (default True)
            overlap_enabled: Whether to enable overlapping segmentation (default True, only used if segmentation_enabled=True)
            segment_only: Stop after fast segmentation for transcription review (default True)

        Returns:
            True if started successfully, False otherwise
        """
        if self.is_running:
            return False

        # Check prerequisites
        if not PIPELINE_SCRIPT.exists():
            self.tracker.state.state = PipelineState.FAILED
            self.tracker.state.errors.append(
                f"Pipeline script not found: {PIPELINE_SCRIPT}"
            )
            return False

        if not INPUT_DIR.exists() or not any(INPUT_DIR.iterdir()):
            self.tracker.state.state = PipelineState.FAILED
            self.tracker.state.errors.append("No videos in input folder")
            return False

        # Generate run ID
        self._run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._cancel_requested = False
        self._on_progress = on_progress
        self._train_kmeans = train_kmeans
        self._golden_model = golden_model
        self._segmentation_enabled = segmentation_enabled
        self._overlap_enabled = overlap_enabled
        self._segment_only = segment_only

        # Reset tracker
        self.tracker.reset(self._run_id)
        self.tracker.state.segment_only = segment_only

        # Copy videos to pipeline input location
        try:
            self._prepare_input()
        except Exception as e:
            self.tracker.mark_failed(f"Failed to prepare input: {e}")
            return False

        # Start pipeline in background thread
        self._monitor_thread = threading.Thread(
            target=self._run_pipeline,
            daemon=True,
        )
        self._monitor_thread.start()

        return True

    def cancel(self) -> bool:
        """Cancel the running pipeline."""
        if not self.is_running:
            return False

        self._cancel_requested = True
        self._terminate_process()
        self.tracker.mark_cancelled()
        self._notify_progress()

        return True

    def reset(self) -> bool:
        """Reset the pipeline state for a fresh start."""
        # Don't reset if pipeline is currently running
        if self.is_running:
            return False

        # Reset all state
        self._cancel_requested = False
        self.process = None
        self._monitor_thread = None
        self._on_progress = None
        self._run_id = None

        # Reset tracker to idle state
        self.tracker.reset(None)

        return True

    def _prepare_input(self):
        """Verify input folder has videos. Pipeline handles the rest."""
        # The pipeline script (step 0.5) handles:
        # - Reading from RAW_DIR (INPUT_DIR passed as argument)
        # - Normalizing videos
        # - Clearing and populating FLAT_VID_DIR
        # So we just need to verify videos exist in INPUT_DIR

        video_count = 0
        for video_file in INPUT_DIR.iterdir():
            if video_file.is_file() and video_file.suffix.lower() in {
                ".mp4", ".mkv", ".webm", ".mov", ".m4v", ".avi"
            }:
                video_count += 1

        if video_count == 0:
            raise RuntimeError("No video files found in input folder")

    def _run_pipeline(self):
        """Run the pipeline subprocess with monitoring."""
        try:
            # Build command - pass INPUT_DIR as the raw videos directory
            # The pipeline script handles normalization and copying to FLAT_VID_DIR
            cmd = [
                "bash",
                str(PIPELINE_SCRIPT),
                str(INPUT_DIR),
            ]

            # Start process
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,  # Line buffered
                env=self._get_env(),
            )

            # Read output lines
            last_output_time = time.time()
            timeout_warned = False

            while True:
                if self._cancel_requested:
                    break

                # Check if process finished
                retcode = self.process.poll()
                if retcode is not None:
                    # Read remaining output
                    remaining = self.process.stdout.read()
                    if remaining:
                        for line in remaining.splitlines():
                            self.tracker.process_line(line)
                            self._notify_progress()

                    if retcode == 0:
                        if self.tracker.state.state != PipelineState.COMPLETED:
                            self.tracker.state.state = PipelineState.COMPLETED
                            self.tracker.state.percent_complete = 100
                    else:
                        self.tracker.mark_failed(
                            f"Pipeline exited with code {retcode}"
                        )
                    break

                # Read line with timeout
                try:
                    line = self.process.stdout.readline()
                    if line:
                        last_output_time = time.time()
                        timeout_warned = False
                        self.tracker.process_line(line)
                        self._notify_progress()
                except Exception:
                    pass

                # Check for stage timeout
                if self.tracker.check_stage_timeout():
                    stage_name = self.tracker.state.current_stage_name
                    self.tracker.mark_failed(
                        f"Stage '{stage_name}' timed out"
                    )
                    self._terminate_process()
                    break

                # Check for overall inactivity (no output for 10 minutes)
                inactivity = time.time() - last_output_time
                if inactivity > 600 and not timeout_warned:
                    self.tracker.state.warnings.append(
                        "No output for 10 minutes - pipeline may be stuck"
                    )
                    timeout_warned = True
                    self._notify_progress()

                time.sleep(0.1)

        except Exception as e:
            self.tracker.mark_failed(f"Pipeline error: {e}")

        finally:
            # Set output path
            self._set_output_path()
            self._notify_progress()

            # Cleanup
            with self._lock:
                self.process = None

    def _get_env(self) -> dict:
        """Get environment variables for pipeline execution."""
        env = os.environ.copy()
        # Add any necessary environment variables
        env["PYTHONUNBUFFERED"] = "1"

        # Pass golden k-means model path if specified
        if self._golden_model:
            env["GOLDEN_KMEANS"] = self._golden_model
            # Don't train k-means if using golden model
            env["TRAIN_KMEANS"] = "0"
        else:
            # Pass k-means training option
            env["TRAIN_KMEANS"] = "1" if self._train_kmeans else "0"

        # Pass segmentation options
        env["SEGMENTATION_ENABLED"] = "1" if self._segmentation_enabled else "0"
        env["OVERLAP_ENABLED"] = "1" if self._overlap_enabled else "0"

        # Pass segment-only option (fast segmentation, then show transcription screen)
        env["SEGMENT_ONLY"] = "1" if self._segment_only else "0"

        return env

    def _terminate_process(self):
        """Gracefully terminate the pipeline process."""
        if self.process is None:
            return

        try:
            # First try SIGTERM
            self.process.terminate()

            # Wait up to 10 seconds
            for _ in range(100):
                if self.process.poll() is not None:
                    return
                time.sleep(0.1)

            # Force kill if still running
            self.process.kill()
            self.process.wait(timeout=5)

        except Exception:
            pass

    def _set_output_path(self):
        """Set the output path after pipeline completion."""
        if not self._run_id:
            return

        # Find the most recent archive directory
        if ARCHIVE_DIR.exists():
            archives = sorted(ARCHIVE_DIR.iterdir(), reverse=True)
            for archive in archives:
                client_outputs = archive / "client_outputs"
                if client_outputs.exists():
                    self.tracker.state.output_path = str(client_outputs)
                    return

    def _notify_progress(self):
        """Notify progress callback if set."""
        if self._on_progress:
            try:
                self._on_progress(self.get_progress())
            except Exception:
                pass


# Singleton instance
_runner: Optional[PipelineRunner] = None


def get_runner() -> PipelineRunner:
    """Get the singleton pipeline runner instance."""
    global _runner
    if _runner is None:
        _runner = PipelineRunner()
    return _runner
