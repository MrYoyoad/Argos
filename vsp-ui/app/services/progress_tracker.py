"""
Progress tracker for pipeline execution.
Parses output lines to detect stage transitions and estimate progress.
"""
import re
import time
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field, asdict

from ..config import (
    PIPELINE_STAGES,
    STAGE_MARKERS,
    ERROR_PATTERNS,
    COMPLETION_MARKER,
    PipelineState,
)


@dataclass
class ProgressState:
    state: str = PipelineState.IDLE
    current_stage_index: int = -1
    current_stage_id: str = ""
    current_stage_name: str = ""
    current_stage_description: str = ""
    stages_completed: int = 0
    total_stages: int = len(PIPELINE_STAGES)
    percent_complete: int = 0
    last_log_line: str = ""
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    run_id: Optional[str] = None
    output_path: Optional[str] = None
    logs: List[str] = field(default_factory=list)
    start_time: Optional[float] = None
    stage_start_time: Optional[float] = None
    segment_only: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "state": self.state,
            "current_stage_index": self.current_stage_index,
            "current_stage_id": self.current_stage_id,
            "current_stage_name": self.current_stage_name,
            "current_stage_description": self.current_stage_description,
            "stages_completed": self.stages_completed,
            "total_stages": self.total_stages,
            "percent_complete": self.percent_complete,
            "last_log_line": self.last_log_line,
            "errors": self.errors,
            "warnings": self.warnings,
            "run_id": self.run_id,
            "output_path": self.output_path,
            "segment_only": self.segment_only,
        }


class ProgressTracker:
    """Tracks progress of the pipeline by parsing output lines."""

    def __init__(self):
        self.state = ProgressState()
        self._compiled_stage_patterns = {
            stage_id: re.compile(pattern)
            for stage_id, pattern in STAGE_MARKERS.items()
        }
        self._compiled_error_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in ERROR_PATTERNS
        ]
        self._completion_pattern = re.compile(COMPLETION_MARKER)
        self._stage_weights = {stage.id: stage.weight for stage in PIPELINE_STAGES}
        self._max_logs = 1000  # Keep last N log lines

    def reset(self, run_id: Optional[str] = None):
        """Reset tracker for a new pipeline run."""
        self.state = ProgressState()
        self.state.run_id = run_id
        self.state.state = PipelineState.RUNNING
        self.state.start_time = time.time()

    def process_line(self, line: str) -> bool:
        """
        Process a single output line from the pipeline.
        Returns True if a stage transition occurred.
        """
        line = line.strip()
        if not line:
            return False

        # Store log line
        self.state.last_log_line = line
        self.state.logs.append(line)
        if len(self.state.logs) > self._max_logs:
            self.state.logs = self.state.logs[-self._max_logs:]

        # Check for completion
        if self._completion_pattern.search(line):
            self._mark_complete()
            return True

        # Check for stage transitions
        stage_changed = False
        for stage_id, pattern in self._compiled_stage_patterns.items():
            if pattern.search(line):
                self._transition_to_stage(stage_id)
                stage_changed = True
                break

        # Check for errors
        for pattern in self._compiled_error_patterns:
            if pattern.search(line):
                self.state.errors.append(line)
                # Keep only last 10 errors
                if len(self.state.errors) > 10:
                    self.state.errors = self.state.errors[-10:]
                break

        # Check for specific warnings (e.g., skipped videos)
        if "Cannot detect any frames" in line or "No face detected" in line:
            self.state.warnings.append(f"Video skipped: {line}")
            if len(self.state.warnings) > 20:
                self.state.warnings = self.state.warnings[-20:]

        # Extract output path if present
        if "Outputs:" in line or "client_outputs" in line:
            # Try to extract path - match anything after "Outputs: " or any path with client_outputs
            path_match = re.search(r"Outputs:\s+(.+)", line)
            if not path_match:
                path_match = re.search(r"(/\S+/client_outputs\S*)", line)
            if path_match:
                self.state.output_path = path_match.group(1).strip()

        # Update progress percentage
        self._update_progress()

        return stage_changed

    def _transition_to_stage(self, stage_id: str):
        """Transition to a new pipeline stage."""
        # Find stage index
        for i, stage in enumerate(PIPELINE_STAGES):
            if stage.id == stage_id:
                self.state.current_stage_index = i
                self.state.current_stage_id = stage.id
                self.state.current_stage_name = stage.name
                self.state.current_stage_description = stage.description
                self.state.stages_completed = i
                self.state.stage_start_time = time.time()
                break

    def _update_progress(self):
        """Update progress percentage based on completed stages."""
        if self.state.current_stage_index < 0:
            self.state.percent_complete = 0
            return

        # Sum weights of completed stages
        completed_weight = 0
        for i, stage in enumerate(PIPELINE_STAGES):
            if i < self.state.current_stage_index:
                completed_weight += stage.weight

        # Add partial weight for current stage (assume 50% through current stage)
        if self.state.current_stage_index < len(PIPELINE_STAGES):
            current_stage = PIPELINE_STAGES[self.state.current_stage_index]
            completed_weight += current_stage.weight * 0.5

        self.state.percent_complete = min(99, int(completed_weight))

    def _mark_complete(self):
        """Mark pipeline as completed."""
        self.state.state = PipelineState.COMPLETED
        self.state.percent_complete = 100
        self.state.stages_completed = len(PIPELINE_STAGES)

    def mark_failed(self, error_message: str):
        """Mark pipeline as failed with error."""
        self.state.state = PipelineState.FAILED
        self.state.errors.append(error_message)

    def mark_cancelled(self):
        """Mark pipeline as cancelled."""
        self.state.state = PipelineState.CANCELLED

    def get_stage_timeout(self) -> int:
        """Get timeout for current stage in seconds."""
        if 0 <= self.state.current_stage_index < len(PIPELINE_STAGES):
            return PIPELINE_STAGES[self.state.current_stage_index].timeout_seconds
        return 3600  # Default 1 hour

    def check_stage_timeout(self) -> bool:
        """Check if current stage has exceeded its timeout."""
        if self.state.stage_start_time is None:
            return False

        elapsed = time.time() - self.state.stage_start_time
        timeout = self.get_stage_timeout()
        return elapsed > timeout

    def get_recent_logs(self, n: int = 50) -> List[str]:
        """Get the most recent N log lines."""
        return self.state.logs[-n:]

    def get_all_logs(self) -> str:
        """Get all logs as a single string."""
        return "\n".join(self.state.logs)
