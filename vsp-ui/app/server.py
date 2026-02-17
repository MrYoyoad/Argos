"""
HTTP server using Python standard library only.
Provides REST API and WebSocket-like polling for progress updates.
"""
import json
import os
import subprocess
import threading
import time
import zipfile
import io
from http.server import HTTPServer, SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Dict, Any, Optional
from urllib.parse import parse_qs, urlparse
import mimetypes
from socketserver import ThreadingMixIn

from .config import (
    SERVER_HOST,
    SERVER_PORT,
    INPUT_DIR,
    PipelineState,
)
from .services.validator import validate_input_folder
from .services.pipeline_runner import get_runner
from .services.transcription_manager import TranscriptionManager

# Initialize transcription manager (module-level singleton)
transcription_mgr = TranscriptionManager()


class VSPRequestHandler(SimpleHTTPRequestHandler):
    """Custom request handler for VSP Pipeline UI."""

    # Static files directory
    STATIC_DIR = Path(__file__).parent / "static"

    def __init__(self, *args, **kwargs):
        # Set directory for static files
        super().__init__(*args, directory=str(self.STATIC_DIR), **kwargs)

    def setup(self):
        """Increase socket timeout for large file uploads."""
        super().setup()
        self.request.settimeout(300)  # 5 minutes

    def log_message(self, format, *args):
        """Suppress default logging."""
        pass

    def send_json(self, data: Dict[str, Any], status: int = 200):
        """Send JSON response."""
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(body))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def send_error_json(self, message: str, status: int = 400):
        """Send error as JSON."""
        self.send_json({"error": message}, status)

    def send_file(self, file_path: Path, content_type: str):
        """Send file with proper headers."""
        try:
            file_size = file_path.stat().st_size
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(file_size))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            with open(file_path, 'rb') as f:
                chunk_size = 8192
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
        except Exception as e:
            print(f"Error sending file {file_path}: {e}")
            self.send_error_json(f"Error serving file: {str(e)}", 500)

    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        """Handle GET requests."""
        parsed = urlparse(self.path)
        path = parsed.path

        # API endpoints
        if path == "/api/status":
            self.handle_status()
        elif path == "/api/progress":
            self.handle_progress()
        elif path == "/api/logs":
            self.handle_logs(parsed.query)
        elif path == "/api/golden-models":
            self.handle_list_golden_models()
        elif path == "/api/download-output":
            self.handle_download_output()
        elif path == "/api/transcription":
            params = parse_qs(parsed.query)
            self.handle_get_transcription(params)
        elif path == "/api/orphaned-transcriptions":
            self.handle_get_orphaned_transcriptions()
        elif path == "/api/segments":
            self.handle_get_segments()
        elif path.startswith("/api/segment-video/"):
            segment_id = path.split("/")[-1]
            self.handle_get_segment_video(segment_id)
        elif path == "/" or path == "/index.html":
            self.serve_static("index.html")
        elif path.startswith("/"):
            # Serve static files
            self.serve_static(path[1:])
        else:
            self.send_error_json("Not found", 404)

    def do_POST(self):
        """Handle POST requests."""
        parsed = urlparse(self.path)
        path = parsed.path

        # Handle file upload separately (multipart/form-data)
        if path == "/api/upload":
            self.handle_upload()
            return

        # Read body if present
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length else ""

        try:
            data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            data = {}

        if path == "/api/validate":
            self.handle_validate()
        elif path == "/api/start":
            self.handle_start(data)
        elif path == "/api/cancel":
            self.handle_cancel()
        elif path == "/api/reset":
            self.handle_reset()
        elif path == "/api/remove-video":
            self.handle_remove_video(data)
        elif path == "/api/transcription":
            self.handle_post_transcription(data)
        elif path == "/api/save-segment-transcription":
            self.handle_save_segment_transcription(data)
        elif path == "/api/open-folder":
            self.handle_open_folder(data)
        else:
            self.send_error_json("Not found", 404)

    def serve_static(self, filename: str):
        """Serve a static file."""
        filepath = self.STATIC_DIR / filename

        if not filepath.exists():
            self.send_error_json("Not found", 404)
            return

        # Get content type
        content_type, _ = mimetypes.guess_type(str(filepath))
        if content_type is None:
            content_type = "application/octet-stream"

        try:
            with open(filepath, "rb") as f:
                content = f.read()

            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", len(content))

            # Add cache-control headers to prevent browser caching
            # This ensures users always get the latest version of static files
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")

            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error_json(f"Error reading file: {e}", 500)

    def handle_status(self):
        """Return current system status."""
        runner = get_runner()

        # Count videos in input folder
        video_count = 0
        if INPUT_DIR.exists():
            for ext in [".mp4", ".mkv", ".webm", ".mov", ".m4v", ".avi"]:
                video_count += len(list(INPUT_DIR.glob(f"*{ext}")))
                video_count += len(list(INPUT_DIR.glob(f"*{ext.upper()}")))

        self.send_json({
            "state": runner.state,
            "input_folder": str(INPUT_DIR),
            "video_count": video_count,
            "is_running": runner.is_running,
        })

    def handle_progress(self):
        """Return current progress state."""
        runner = get_runner()
        self.send_json(runner.get_progress())

    def handle_logs(self, query: str):
        """Return recent log lines."""
        params = parse_qs(query)
        n = int(params.get("n", ["50"])[0])
        all_logs = "all" in params

        runner = get_runner()

        if all_logs:
            self.send_json({"logs": runner.get_all_logs()})
        else:
            self.send_json({"logs": runner.get_logs(n)})

    def handle_validate(self):
        """Validate videos in input folder and load existing segments."""
        try:
            result = validate_input_folder()
            response = result.to_dict()

            # Also check for existing segments from previous runs
            from .config import AUTO_AVSR_DIR, SEGMENT_DURATION
            fast_seg_dir = AUTO_AVSR_DIR / f"preprocessed_flat_seg{SEGMENT_DURATION}" / "fast_segments"
            full_seg_dir = AUTO_AVSR_DIR / f"preprocessed_flat_seg{SEGMENT_DURATION}" / "flat" / f"flat_video_seg{SEGMENT_DURATION}s"

            existing_segments = []

            # Check for fast_segments
            if fast_seg_dir.exists():
                existing_segments = self._load_segment_info(fast_seg_dir)
            elif full_seg_dir.exists():
                existing_segments = self._load_segment_info(full_seg_dir)

            response['existing_segments'] = existing_segments
            response['existing_segments_count'] = len(existing_segments)

            self.send_json(response)
        except Exception as e:
            self.send_error_json(f"Validation error: {e}", 500)

    def _load_segment_info(self, segment_dir: Path) -> list:
        """Load info about existing segments."""
        from .config import INPUT_DIR, AUTO_AVSR_DIR, SEGMENT_DURATION
        from .services.transcription_manager import TranscriptionManager
        transcription_mgr = TranscriptionManager()

        segments = []
        for video_file in sorted(segment_dir.glob('*.mp4')):
            segment_id = video_file.stem

            # Check for transcription in .transcriptions folder first
            transcription_wrd = INPUT_DIR / ".transcriptions" / f"{segment_id}.wrd"
            has_transcription = transcription_wrd.exists()
            transcription_type = None

            if has_transcription:
                info = transcription_mgr.get_transcription_info(f"{segment_id}.mp4")
                transcription_type = info.type if info else "manual"
            else:
                # Fallback: check preprocessed text directory
                text_dir = AUTO_AVSR_DIR / f"preprocessed_flat_seg{SEGMENT_DURATION}" / "flat" / f"flat_text_seg{SEGMENT_DURATION}s"
                transcription_file = text_dir / f"{segment_id}.txt"
                if transcription_file.exists():
                    has_transcription = True
                    transcription_type = "manual"  # Preprocessed text files are manual transcriptions

            # Get duration
            duration = 0.0
            try:
                import subprocess
                result = subprocess.run([
                    'ffprobe', '-v', 'error',
                    '-show_entries', 'format=duration',
                    '-of', 'default=noprint_wrappers=1:nokey=1',
                    str(video_file)
                ], capture_output=True, text=True, timeout=10)
                duration = float(result.stdout.strip())
            except Exception:
                pass

            segments.append({
                'id': segment_id,
                'filename': video_file.name,
                'duration': duration,
                'has_transcription': has_transcription,
                'transcription_type': transcription_type
            })

        return segments

    def handle_list_golden_models(self):
        """List all available golden k-means models."""
        try:
            golden_dir = Path.home() / "VSP-LLM" / "golden_kmeans"
            models = []

            if golden_dir.exists():
                for model_file in sorted(golden_dir.glob("*.bin")):
                    stat = model_file.stat()
                    models.append({
                        "name": model_file.name,
                        "path": str(model_file),
                        "size": stat.st_size,
                        "created": stat.st_mtime
                    })

            self.send_json({"models": models})
        except Exception as e:
            self.send_error_json(f"Error listing golden models: {e}", 500)

    def handle_start(self, data: Dict[str, Any] = None):
        """Start pipeline execution."""
        runner = get_runner()

        if runner.is_running:
            self.send_error_json("Pipeline is already running", 400)
            return

        # Get options from request
        if data is None:
            data = {}
        train_kmeans = data.get('train_kmeans', True)
        golden_model = data.get('golden_model', None)
        segmentation_enabled = data.get('segmentation_enabled', True)
        overlap_enabled = data.get('overlap_enabled', True)
        segment_only = data.get('segment_only', True)  # Default: always segment first

        success = runner.start(
            train_kmeans=train_kmeans,
            golden_model=golden_model,
            segmentation_enabled=segmentation_enabled,
            overlap_enabled=overlap_enabled,
            segment_only=segment_only
        )

        if success:
            self.send_json({
                "success": True,
                "message": "Pipeline started",
                "run_id": runner.tracker.state.run_id,
            })
        else:
            self.send_json({
                "success": False,
                "message": "Failed to start pipeline",
                "errors": runner.tracker.state.errors,
            }, 400)

    def handle_cancel(self):
        """Cancel running pipeline."""
        runner = get_runner()

        if not runner.is_running:
            self.send_error_json("No pipeline running", 400)
            return

        success = runner.cancel()
        self.send_json({
            "success": success,
            "message": "Pipeline cancelled" if success else "Failed to cancel",
        })

    def handle_reset(self):
        """Reset pipeline state for a fresh start."""
        runner = get_runner()

        if runner.is_running:
            self.send_error_json("Cannot reset while pipeline is running", 400)
            return

        success = runner.reset()
        self.send_json({
            "success": success,
            "message": "Pipeline reset" if success else "Failed to reset",
        })

    def handle_remove_video(self, data: Dict[str, Any]):
        """Move a video file to excluded folder (not permanently deleted)."""
        filename = data.get("filename")

        if not filename:
            self.send_error_json("No filename provided", 400)
            return

        # Security: ensure filename doesn't contain path traversal
        if ".." in filename or "/" in filename or "\\" in filename:
            self.send_error_json("Invalid filename", 400)
            return

        video_path = INPUT_DIR / filename

        if not video_path.exists():
            self.send_error_json(f"Video not found: {filename}", 404)
            return

        # Create excluded folder
        excluded_dir = INPUT_DIR / ".excluded"
        excluded_dir.mkdir(exist_ok=True)

        try:
            # Move video to excluded folder instead of deleting
            excluded_path = excluded_dir / filename
            video_path.rename(excluded_path)
            self.send_json({
                "success": True,
                "message": f"Excluded {filename}",
            })
        except Exception as e:
            self.send_error_json(f"Failed to exclude video: {e}", 500)

    def handle_open_folder(self, data: Dict[str, Any]):
        """Open a folder in the file manager."""
        folder_type = data.get("type", "input")

        if folder_type == "input":
            folder_path = INPUT_DIR
        elif folder_type == "output":
            runner = get_runner()
            output_path = runner.tracker.state.output_path
            if output_path:
                folder_path = Path(output_path)
            else:
                self.send_error_json("No output folder available", 400)
                return
        else:
            self.send_error_json(f"Unknown folder type: {folder_type}", 400)
            return

        # Ensure folder exists
        folder_path.mkdir(parents=True, exist_ok=True)

        # Try to open folder
        success = open_folder(folder_path)

        self.send_json({
            "success": success,
            "path": str(folder_path),
            "message": "Folder opened" if success else "Could not open folder automatically",
        })

    def handle_get_transcription(self, params: Dict[str, list]):
        """GET /api/transcription?filename=video.mp4 - Get transcription text."""
        filename = params.get('filename', [''])[0]

        # Security: validate filename
        if not filename or '/' in filename or '\\' in filename or '..' in filename:
            self.send_error_json("Invalid filename", 400)
            return

        text = transcription_mgr.get_transcription(filename)
        info = transcription_mgr.get_transcription_info(filename)

        if text is None:
            self.send_json({'text': None})
            return

        self.send_json({
            'text': text,
            'type': info.type,
            'created_at': info.created_at,
            'word_count': info.word_count,
        })

    def handle_post_transcription(self, data: Dict[str, Any]):
        """POST /api/transcription - Save or delete transcription."""
        # Check if this is a delete request (has 'delete' flag or no 'text' field)
        if data.get('delete') or ('text' not in data and 'filename' in data):
            self._handle_delete_transcription(data)
            return

        filename = data.get('filename')
        text = data.get('text', '').strip()

        # Security: validate filename
        if not filename or '/' in filename or '\\' in filename or '..' in filename:
            self.send_json({'success': False, 'error': 'Invalid filename'}, 400)
            return

        if not text:
            self.send_json({'success': False, 'error': 'Text cannot be empty'}, 400)
            return

        # Check if editing existing auto transcription → change to manual
        existing_info = transcription_mgr.get_transcription_info(filename)
        if existing_info and existing_info.type == "auto":
            transcription_type = "manual"  # User edited an auto transcription
        else:
            transcription_type = data.get('type', 'manual')

        result = transcription_mgr.save_transcription(filename, text, transcription_type)
        result['type'] = transcription_type

        self.send_json(result)

    def _handle_delete_transcription(self, data: Dict[str, Any]):
        """DELETE transcription."""
        filename = data.get('filename')

        # Security: validate filename
        if not filename or '/' in filename or '\\' in filename or '..' in filename:
            self.send_json({'success': False, 'error': 'Invalid filename'}, 400)
            return

        success = transcription_mgr.delete_transcription(filename)
        self.send_json({'success': success})

    def handle_get_orphaned_transcriptions(self):
        """GET /api/orphaned-transcriptions - Get list of orphaned transcriptions."""
        # Get current valid videos from input folder
        from .services.validator import get_video_files

        try:
            valid_files = get_video_files()
            valid_filenames = [f.name for f in valid_files]

            orphaned = transcription_mgr.get_orphaned_transcriptions(valid_filenames)

            self.send_json({
                'orphaned': [
                    {
                        'filename': o.filename,
                        'type': o.type,
                        'created_at': o.created_at,
                        'word_count': o.word_count,
                    }
                    for o in orphaned
                ]
            })
        except Exception as e:
            self.send_error_json(f"Failed to get orphaned transcriptions: {e}", 500)

    def handle_get_segments(self):
        """GET /api/segments - Get list of segments (from fast segmentation or full preprocessing)."""
        from .config import AUTO_AVSR_DIR, SEGMENT_DURATION
        import json

        # First check for fast_segments (from SEGMENT_ONLY mode)
        fast_seg_dir = AUTO_AVSR_DIR / f"preprocessed_flat_seg{SEGMENT_DURATION}" / "fast_segments"

        # Check for fully preprocessed segments (segmented videos)
        full_seg_dir = AUTO_AVSR_DIR / f"preprocessed_flat_seg{SEGMENT_DURATION}" / "flat" / f"flat_video_seg{SEGMENT_DURATION}s"

        # Check for whole videos (non-segmented mode)
        whole_vid_dir = AUTO_AVSR_DIR / f"preprocessed_flat_seg{SEGMENT_DURATION}" / "flat" / "flat_video_whole"

        # Determine which directory to use (priority: fast_segments > segmented > whole)
        if fast_seg_dir.exists() and (fast_seg_dir / 'segment_metadata.json').exists():
            segment_dir = fast_seg_dir
            use_fast_segments = True
        elif full_seg_dir.exists():
            segment_dir = full_seg_dir
            use_fast_segments = False
        elif whole_vid_dir.exists():
            segment_dir = whole_vid_dir
            use_fast_segments = False
        else:
            self.send_json({
                'segments': [],
                'message': 'No segments found. Run preprocessing first.'
            })
            return

        # List all segment videos
        segments = []
        from .services.transcription_manager import TranscriptionManager
        transcription_mgr = TranscriptionManager()

        for video_file in sorted(segment_dir.glob('*.mp4')):
            segment_id = video_file.stem

            # Check transcription in .transcriptions folder first (preferred)
            transcription_wrd = INPUT_DIR / ".transcriptions" / f"{segment_id}.wrd"
            has_transcription = False
            transcription_text = ""
            transcription_type = None

            if transcription_wrd.exists():
                has_transcription = True
                try:
                    with open(transcription_wrd, 'r') as f:
                        words = [line.strip() for line in f if line.strip()]
                        transcription_text = " ".join(words)
                except Exception:
                    pass

                # Get transcription type from metadata
                info = transcription_mgr.get_transcription_info(f"{segment_id}.mp4")
                transcription_type = info.type if info else "manual"
            else:
                # Fallback: check preprocessed text directory
                # Try segmented text directory first
                text_dir_seg = AUTO_AVSR_DIR / f"preprocessed_flat_seg{SEGMENT_DURATION}" / "flat" / f"flat_text_seg{SEGMENT_DURATION}s"
                # Try whole video text directory (non-segmented mode)
                text_dir_whole = AUTO_AVSR_DIR / f"preprocessed_flat_seg{SEGMENT_DURATION}" / "flat" / "flat_text_whole"

                transcription_file = None
                if text_dir_seg.exists():
                    transcription_file = text_dir_seg / f"{segment_id}.txt"
                elif text_dir_whole.exists():
                    transcription_file = text_dir_whole / f"{segment_id}.txt"

                if transcription_file and transcription_file.exists():
                    has_transcription = True
                    transcription_type = "manual"  # Preprocessed text files are manual transcriptions
                    try:
                        with open(transcription_file, 'r') as f:
                            words = [line.strip() for line in f if line.strip()]
                            transcription_text = " ".join(words)
                    except Exception:
                        pass

            # Get video duration using ffprobe
            duration = 0.0
            try:
                import subprocess
                result = subprocess.run([
                    'ffprobe', '-v', 'error',
                    '-show_entries', 'format=duration',
                    '-of', 'default=noprint_wrappers=1:nokey=1',
                    str(video_file)
                ], capture_output=True, text=True)
                duration = float(result.stdout.strip())
            except Exception:
                pass

            segments.append({
                'id': segment_id,
                'filename': video_file.name,
                'duration': duration,
                'has_transcription': has_transcription,
                'transcription': transcription_text,
                'transcription_type': transcription_type
            })

        self.send_json({
            'segments': segments,
            'total': len(segments),
            'transcribed': sum(1 for s in segments if s['has_transcription'])
        })

    def handle_get_segment_video(self, segment_id: str):
        """GET /api/segment-video/<segment_id> - Serve segment video file."""
        from .config import AUTO_AVSR_DIR, SEGMENT_DURATION

        # Security: prevent path traversal
        if '..' in segment_id or '/' in segment_id or '\\' in segment_id:
            self.send_error_json("Invalid segment ID", 400)
            return

        try:
            # Check fast_segments first (from SEGMENT_ONLY mode)
            fast_seg_dir = AUTO_AVSR_DIR / f"preprocessed_flat_seg{SEGMENT_DURATION}" / "fast_segments"
            fast_seg_file = fast_seg_dir / f"{segment_id}.mp4"

            if fast_seg_file.exists():
                # Serve the fast segment directly (already a complete video)
                self.send_file(fast_seg_file, 'video/mp4')
                return

            # Fallback: check preprocessed segments
            full_seg_dir = AUTO_AVSR_DIR / f"preprocessed_flat_seg{SEGMENT_DURATION}" / "flat" / f"flat_video_seg{SEGMENT_DURATION}s"
            full_seg_file = full_seg_dir / f"{segment_id}.mp4"

            if full_seg_file.exists():
                # Serve the preprocessed segment
                self.send_file(full_seg_file, 'video/mp4')
                return

            # Not found in either location
            self.send_error_json("Segment video not found", 404)

        except Exception as e:
            print(f"Error serving segment video: {e}")
            import traceback
            traceback.print_exc()
            self.send_error_json(f"Error serving video: {str(e)}", 500)
            if video_name not in metadata:
                self.send_error_json(f"Video not found in metadata: {video_name}", 404)
                return

            video_meta = metadata[video_name]
            segments = video_meta['segments']

            # Find the segment by index
            segment = None
            for seg in segments:
                if seg['index'] == seg_index:
                    segment = seg
                    break

            if not segment:
                self.send_error_json(f"Segment index {seg_index} not found", 404)
                return

            # Get original video file
            original_video = AUTO_AVSR_DIR / "flat" / f"{video_name}.mp4"

            if not original_video.exists():
                self.send_error_json(f"Original video not found: {video_name}.mp4", 404)
                return

            # Extract segment using ffmpeg
            start_time = segment['start_sec']
            duration = segment['duration']

            # Create temporary file for the segment
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
                tmp_path = tmp.name

            try:
                # Use ffmpeg to extract the segment
                cmd = [
                    'ffmpeg', '-y',
                    '-ss', str(start_time),
                    '-i', str(original_video),
                    '-t', str(duration),
                    '-c', 'copy',  # Copy codec (fast, no re-encoding)
                    '-avoid_negative_ts', 'make_zero',
                    tmp_path
                ]

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    timeout=30
                )

                if result.returncode != 0:
                    # Fallback: try with re-encoding if copy fails
                    cmd = [
                        'ffmpeg', '-y',
                        '-ss', str(start_time),
                        '-i', str(original_video),
                        '-t', str(duration),
                        '-c:v', 'libx264',
                        '-c:a', 'aac',
                        '-preset', 'ultrafast',
                        tmp_path
                    ]
                    result = subprocess.run(cmd, capture_output=True, timeout=30)

                    if result.returncode != 0:
                        raise Exception(f"ffmpeg failed: {result.stderr.decode()}")

                # Read the extracted segment
                with open(tmp_path, 'rb') as f:
                    video_data = f.read()

                # Send video
                self.send_response(200)
                self.send_header('Content-Type', 'video/mp4')
                self.send_header('Content-Length', str(len(video_data)))
                self.send_header('Accept-Ranges', 'bytes')
                self.end_headers()
                self.wfile.write(video_data)

            finally:
                # Clean up temp file
                import os
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass

        except Exception as e:
            self.send_error_json(f"Failed to serve video segment: {e}", 500)

    def handle_save_segment_transcription(self, data: Dict[str, Any]):
        """POST /api/save-segment-transcription - Save transcription for a segment."""
        from .config import AUTO_AVSR_DIR, SEGMENT_DURATION
        import re

        segment_id = data.get('segment_id')
        transcription = data.get('transcription', '')

        if not segment_id:
            self.send_error_json("Missing segment_id", 400)
            return

        # Security: prevent path traversal
        if '..' in segment_id or '/' in segment_id or '\\' in segment_id:
            self.send_error_json("Invalid segment ID", 400)
            return

        # Normalize transcription (lowercase, alphanumeric + apostrophes only)
        transcription = transcription.lower()
        transcription = re.sub(r"[^a-z0-9'\s]", ' ', transcription)
        transcription = re.sub(r'\s+', ' ', transcription)
        transcription = transcription.strip()

        if not transcription:
            self.send_error_json("Transcription cannot be empty", 400)
            return

        # Save transcription to unified .transcriptions directory as .wrd file
        from .services.transcription_manager import TranscriptionManager

        try:
            transcription_mgr = TranscriptionManager()
            filename = f"{segment_id}.mp4"

            # Save as manual transcription
            transcription_mgr.save_transcription(filename, transcription, transcription_type='manual')

            words = transcription.split()
            self.send_json({
                'success': True,
                'message': 'Transcription saved',
                'word_count': len(words)
            })
        except Exception as e:
            self.send_error_json(f"Failed to save transcription: {e}", 500)

    def handle_download_output(self):
        """Download output folder as a zip file."""
        try:
            runner = get_runner()
            output_path = runner.tracker.state.output_path

            if not output_path:
                self.send_error_json("No output folder available", 404)
                return

            output_dir = Path(output_path)
            if not output_dir.exists():
                self.send_error_json(f"Output folder not found: {output_path}", 404)
                return

            # Create zip file in memory
            zip_buffer = io.BytesIO()

            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # Add all files from the output directory
                for file_path in output_dir.rglob('*'):
                    if file_path.is_file():
                        # Store relative path in zip
                        arcname = file_path.relative_to(output_dir.parent)
                        zip_file.write(file_path, arcname)

            # Get zip contents
            zip_data = zip_buffer.getvalue()

            # Send zip file as download
            self.send_response(200)
            self.send_header("Content-Type", "application/zip")
            self.send_header("Content-Length", len(zip_data))
            self.send_header("Content-Disposition", f'attachment; filename="vsp_output_{output_dir.name}.zip"')
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(zip_data)

        except Exception as e:
            self.send_error_json(f"Failed to create download: {e}", 500)

    def handle_upload(self):
        """Handle file upload via multipart/form-data.

        Uses manual multipart parsing instead of deprecated cgi.FieldStorage
        for reliable binary file uploads across all Python versions.
        """
        try:
            content_type = self.headers.get('Content-Type', '')
            content_length = int(self.headers.get('Content-Length', 0))

            if 'multipart/form-data' not in content_type:
                self.send_error_json("Expected multipart/form-data", 400)
                return

            if content_length <= 0:
                self.send_error_json("No content received", 400)
                return

            # Extract boundary from Content-Type header
            boundary = None
            for part in content_type.split(';'):
                part = part.strip()
                if part.startswith('boundary='):
                    boundary = part[len('boundary='):]
                    # Remove quotes if present
                    if boundary.startswith('"') and boundary.endswith('"'):
                        boundary = boundary[1:-1]
                    break

            if not boundary:
                self.send_error_json("Missing multipart boundary", 400)
                return

            # Read body in chunks (prevents timeout/OOM on large video files)
            size_str = self._format_file_size(content_length)
            print(f"[UPLOAD] Starting: {content_length} bytes ({size_str})")
            CHUNK_SIZE = 1024 * 1024  # 1 MB
            body = bytearray()
            bytes_read = 0
            while bytes_read < content_length:
                to_read = min(CHUNK_SIZE, content_length - bytes_read)
                chunk = self.rfile.read(to_read)
                if not chunk:
                    break
                body.extend(chunk)
                bytes_read += len(chunk)
            body = bytes(body)
            print(f"[UPLOAD] Read complete: {bytes_read} bytes")
            boundary_bytes = boundary.encode('utf-8')
            delimiter = b'--' + boundary_bytes

            # Split body by boundary
            parts = body.split(delimiter)

            # Find the file part (skip first empty part and last closing part)
            filename = None
            file_data = None

            for part in parts:
                if not part or part == b'--\r\n' or part == b'--':
                    continue

                # Split headers from body (separated by \r\n\r\n)
                header_end = part.find(b'\r\n\r\n')
                if header_end == -1:
                    continue

                headers_raw = part[:header_end].decode('utf-8', errors='replace')
                # File data starts after \r\n\r\n, ends before trailing \r\n
                file_body = part[header_end + 4:]
                if file_body.endswith(b'\r\n'):
                    file_body = file_body[:-2]

                # Parse Content-Disposition to find filename
                if 'name="file"' in headers_raw:
                    for header_line in headers_raw.split('\r\n'):
                        if 'filename=' in header_line:
                            # Extract filename from: Content-Disposition: form-data; name="file"; filename="video.mp4"
                            fn_start = header_line.find('filename=')
                            if fn_start != -1:
                                fn_value = header_line[fn_start + len('filename='):]
                                fn_value = fn_value.strip()
                                if fn_value.startswith('"') and '"' in fn_value[1:]:
                                    filename = fn_value[1:fn_value.index('"', 1)]
                                else:
                                    filename = fn_value.split(';')[0].strip()
                    file_data = file_body

            if not filename:
                self.send_error_json("No filename provided", 400)
                return

            if file_data is None:
                self.send_error_json("No file data received", 400)
                return

            filename = os.path.basename(filename)

            # Security: validate filename
            if not self._is_safe_filename(filename):
                self.send_error_json(f"Invalid filename: {filename}", 400)
                return

            # Validate file extension
            if not self._is_valid_video_extension(filename):
                self.send_error_json(f"Invalid file type. Supported: mp4, mkv, webm, mov, m4v, avi", 400)
                return

            # Ensure input directory exists
            INPUT_DIR.mkdir(parents=True, exist_ok=True)

            # Save file to input directory
            file_path = INPUT_DIR / filename
            with open(file_path, 'wb') as output_file:
                output_file.write(file_data)

            file_size = len(file_data)
            size_str = self._format_file_size(file_size)
            print(f"[UPLOAD] Complete: {filename} ({size_str})")

            self.send_json({
                "success": True,
                "filename": filename,
                "message": f"Uploaded {size_str}",
                "size": file_size,
            })

        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"[UPLOAD] Failed: {str(e)}")
            self.send_error_json(f"Upload failed: {str(e)}", 500)

    def _is_safe_filename(self, filename: str) -> bool:
        """Check if filename is safe (no path traversal)."""
        if not filename:
            return False
        if ".." in filename or "/" in filename or "\\" in filename:
            return False
        return True

    def _is_valid_video_extension(self, filename: str) -> bool:
        """Check if file has a valid video extension."""
        valid_extensions = {'.mp4', '.mkv', '.webm', '.mov', '.m4v', '.avi'}
        ext = Path(filename).suffix.lower()
        return ext in valid_extensions

    def _format_file_size(self, size: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"


def open_folder(path: Path) -> bool:
    """Try to open a folder in the system file manager."""
    import time
    path_str = str(path)

    # Build environment with display variables for GUI access
    env = os.environ.copy()

    # Try various methods (gio is most reliable on modern GNOME)
    commands = [
        ["gio", "open", path_str],
        ["xdg-open", path_str],
        ["nautilus", path_str],
        ["nemo", path_str],
        ["thunar", path_str],
        ["dolphin", path_str],
        ["pcmanfm", path_str],
    ]

    for cmd in commands:
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                env=env,
            )
            # Wait briefly to check if command failed immediately
            time.sleep(0.3)
            retcode = proc.poll()
            if retcode is None or retcode == 0:
                return True  # Still running or exited successfully
            # Non-zero exit - try next command
        except (FileNotFoundError, PermissionError):
            continue

    return False


def open_browser(url: str) -> bool:
    """Try to open a URL in the default browser."""
    commands = [
        ["xdg-open", url],
        ["firefox", url],
        ["chromium-browser", url],
        ["google-chrome", url],
    ]

    for cmd in commands:
        try:
            subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        except (FileNotFoundError, PermissionError):
            continue

    return False


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """HTTP server that handles each request in a separate thread."""
    allow_reuse_address = True
    daemon_threads = True  # Don't wait for threads on shutdown


def run_server(host: str = SERVER_HOST, port: int = SERVER_PORT):
    """Run the HTTP server."""
    # Ensure input directory exists
    INPUT_DIR.mkdir(parents=True, exist_ok=True)

    server = ThreadedHTTPServer((host, port), VSPRequestHandler)
    print(f"VSP Pipeline UI running at http://{host}:{port}")
    print(f"Input folder: {INPUT_DIR}")
    print("Press Ctrl+C to stop")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()


if __name__ == "__main__":
    run_server()
