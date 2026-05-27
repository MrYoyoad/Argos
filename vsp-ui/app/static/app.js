/**
 * VSP Pipeline UI - Frontend Logic
 * Uses polling for progress updates (no WebSocket dependencies)
 */

// State
let currentScreen = 'welcome';
let validationResult = null;
let pollInterval = null;
let logsVisible = false;
let isUploading = false;
let uploadResults = [];
let currentTranscriptionFilename = null;
let currentTranscriptionType = null;
let orphanedTranscriptions = [];

// DOM Elements
const screens = {
    welcome: document.getElementById('welcome-screen'),
    validation: document.getElementById('validation-screen'),  // Legacy - validation screen
    segmentReview: document.getElementById('segment-review-screen'),  // New - segment review after segmentation
    processing: document.getElementById('processing-screen'),
    transcription: document.getElementById('transcription-screen'),
    complete: document.getElementById('complete-screen'),
    error: document.getElementById('error-screen'),
};

const elements = {
    statusBadge: document.getElementById('status-badge'),
    inputPath: document.getElementById('input-path'),
    videoCountText: document.getElementById('video-count-text'),

    // Upload
    dropZoneOverlay: document.getElementById('drop-zone-overlay'),
    uploadProgressSection: document.getElementById('upload-progress-section'),
    uploadStatus: document.getElementById('upload-status'),
    uploadFilesList: document.getElementById('upload-files-list'),

    // Validation
    warningsContainer: document.getElementById('warnings-container'),
    warningsList: document.getElementById('warnings-list'),
    validCount: document.getElementById('valid-count'),
    segmentCount: document.getElementById('segment-count'),
    totalDuration: document.getElementById('total-duration'),
    validVideosList: document.getElementById('valid-videos-list'),
    invalidVideosSection: document.getElementById('invalid-videos-section'),
    invalidVideosList: document.getElementById('invalid-videos-list'),

    // Progress
    progressFill: document.getElementById('progress-fill'),
    progressPercent: document.getElementById('progress-percent'),
    stageName: document.getElementById('stage-name'),
    stageDescription: document.getElementById('stage-description'),
    decodeCounter: document.getElementById('decode-counter'),
    decodeDone: document.getElementById('decode-done'),
    decodeTotal: document.getElementById('decode-total'),
    logsContainer: document.getElementById('logs-container'),
    logsOutput: document.getElementById('logs-output'),

    // Complete
    outputPath: document.getElementById('output-path'),

    // Error
    errorMessage: document.getElementById('error-message'),
    errorDetails: document.getElementById('error-details'),
    errorLogsContainer: document.getElementById('error-logs-container'),
    errorLogsOutput: document.getElementById('error-logs-output'),
};

// API Functions
async function api(endpoint, method = 'GET', data = null) {
    const options = {
        method,
        headers: { 'Content-Type': 'application/json' },
    };

    if (data) {
        options.body = JSON.stringify(data);
    }

    // Add timeout to prevent hanging
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout

    try {
        const response = await fetch(`/api/${endpoint}`, {
            ...options,
            signal: controller.signal
        });
        clearTimeout(timeoutId);
        return await response.json();
    } catch (error) {
        clearTimeout(timeoutId);
        console.error(`API error (${endpoint}):`, error);
        if (error.name === 'AbortError') {
            return { error: 'Request timeout - server did not respond' };
        }
        return { error: error.message };
    }
}

// Screen Management
function showScreen(screenName) {
    console.log('showScreen called with:', screenName);
    console.log('Available screens:', Object.keys(screens));

    // A1 audit: stop polling whenever we leave the processing screen for a
    // non-processing one. Old code only stopped polling on state transitions
    // (completed/failed/cancelled). If the user navigated away mid-run,
    // pollInterval would keep firing /api/progress every 500ms forever and
    // could even bounce the user back to a stale screen.
    if (currentScreen === 'processing' && screenName !== 'processing') {
        if (typeof stopProgressPolling === 'function') {
            stopProgressPolling();
        }
    }

    Object.keys(screens).forEach(name => {
        const screen = screens[name];
        if (screen) {
            screens[name].classList.toggle('active', name === screenName);
        } else {
            console.warn(`Screen element not found for: ${name}`);
        }
    });
    currentScreen = screenName;

    // Update status badge
    updateStatusBadge(screenName);
}

function updateStatusBadge(screen) {
    const badge = elements.statusBadge;
    badge.className = 'badge';

    switch (screen) {
        case 'welcome':
        case 'validation':
        case 'segmentReview':  // Add segment review to ready state
            badge.textContent = 'Ready';
            break;
        case 'processing':
            badge.textContent = 'Processing';
            badge.classList.add('running');
            break;
        case 'transcription':
            badge.textContent = 'Transcribing';
            badge.classList.add('running');
            break;
        case 'complete':
            badge.textContent = 'Complete';
            badge.classList.add('complete');
            break;
        case 'error':
            badge.textContent = 'Error';
            badge.classList.add('error');
            break;
    }
}

// Format Helpers
function formatDuration(seconds) {
    if (seconds < 60) {
        return `${seconds.toFixed(1)}s`;
    } else if (seconds < 3600) {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}m ${secs}s`;
    } else {
        const hours = Math.floor(seconds / 3600);
        const mins = Math.floor((seconds % 3600) / 60);
        return `${hours}h ${mins}m`;
    }
}

// Welcome Screen
async function refreshStatus() {
    const status = await api('status');

    if (status.error) {
        // A1 audit: never leave the UI in a dead-end "Error connecting" state.
        // Auto-retry every 2s so a transient failure self-heals.
        console.warn('[A1 audit] refreshStatus: status error, retrying in 2s:', status.error);
        elements.videoCountText.textContent = 'Cannot reach server — retrying…';
        clearTimeout(refreshStatus._retry);
        refreshStatus._retry = setTimeout(refreshStatus, 2000);
        return;
    }
    // Clear any pending retry timer on a successful poll.
    if (refreshStatus._retry) {
        clearTimeout(refreshStatus._retry);
        refreshStatus._retry = null;
    }

    // Prefer the host-side path (e.g. C:\Users\Amos\vsp-input) over the
    // container's internal /data/in — the latter is meaningless to the
    // end user on Windows.
    elements.inputPath.textContent = status.host_input_folder || status.input_folder;

    let countText;
    if (status.video_count === 0) {
        countText = 'No videos detected — drag videos here or copy them into the folder above';
        document.getElementById('btn-start-processing').disabled = true;
    } else {
        countText = `${status.video_count} video(s) ready for processing`;
        document.getElementById('btn-start-processing').disabled = false;
    }
    if (status.archived_count && status.archived_count > 0) {
        countText += ` · ${status.archived_count} archived`;
    }
    elements.videoCountText.textContent = countText;

    // Surface the "Show archived" toggle only when there are archived videos.
    const toggleBtn = document.getElementById('btn-toggle-archived');
    if (toggleBtn) {
        toggleBtn.style.display = (status.archived_count > 0) ? 'inline-block' : 'none';
    }

    // If pipeline is running, show processing screen
    if (status.is_running) {
        showScreen('processing');
        startProgressPolling();
    } else if (status.state === 'completed') {
        // Check if we have a completed segment-only run
        const progress = await api('progress');
        if (progress.segment_only) {
            console.log('Detected completed segment-only run, loading segments...');
            await loadAndDisplaySegments();
        }
    }
}



async function inspectVideos() {
    const btn = document.getElementById('btn-inspect-videos');
    const section = document.getElementById('video-inspection-section');
    const list = document.getElementById('inspection-videos-list');

    btn.disabled = true;
    btn.textContent = 'Loading...';

    try {
        // Validate to get video list
        const result = await api('validate', 'POST');

        if (result.error) {
            alert(`Failed to load videos: ${result.error}`);
            return;
        }

        // Store for removeVideo function
        validationResult = result;

        // Display videos
        list.innerHTML = result.valid_videos
            .map((v, index) => `
                <li>
                    <div class="video-list-item">
                        <div class="video-info">
                            <span class="video-name">${escapeHtml(v.filename)}</span>
                            <span class="video-duration">${formatDuration(v.duration_seconds)}</span>
                            ${v.has_transcription
                                ? `<span class="badge-${v.transcription_type}">[${v.transcription_type.toUpperCase()}]</span>`
                                : ''}
                        </div>
                        <div class="video-actions">
                            <button class="btn-remove" data-index="${index}" title="Archive (move to .excluded; can be restored)">
                                Archive
                            </button>
                        </div>
                    </div>
                </li>
            `)
            .join('');

        // Add event listeners to remove buttons
        list.querySelectorAll('.btn-remove').forEach(btn => {
            btn.addEventListener('click', async () => {
                const index = parseInt(btn.dataset.index);
                await removeVideoFromInspection(index);
            });
        });

        // Show inspection section
        section.style.display = 'block';

    } finally {
        btn.disabled = false;
        btn.textContent = 'Inspect Videos';
    }
}

async function removeVideoFromInspection(index) {
    if (!validationResult) return;

    const video = validationResult.valid_videos[index];

    // Confirm archive
    if (!confirm(`Archive "${video.filename}"?\n\nThe pipeline will not process it. You can restore it later from the Archived section.`)) {
        return;
    }

    // Call API to move the file to .excluded (archive)
    const result = await api('remove-video', 'POST', { filename: video.filename });

    if (!result.success) {
        alert(`Failed to archive video: ${result.error || 'Unknown error'}`);
        return;
    }

    // Remove from list and refresh display
    validationResult.valid_videos.splice(index, 1);

    // Re-render inspection list
    const list = document.getElementById('inspection-videos-list');
    list.innerHTML = validationResult.valid_videos
        .map((v, idx) => `
            <li>
                <div class="video-list-item">
                    <div class="video-info">
                        <span class="video-name">${escapeHtml(v.filename)}</span>
                        <span class="video-duration">${formatDuration(v.duration_seconds)}</span>
                        ${v.has_transcription
                            ? `<span class="badge-${v.transcription_type}">[${v.transcription_type.toUpperCase()}]</span>`
                            : ''}
                    </div>
                    <div class="video-actions">
                        <button class="btn-remove" data-index="${idx}" title="Archive (move to .excluded; can be restored)">
                            Archive
                        </button>
                    </div>
                </div>
            </li>
        `)
        .join('');

    // Re-attach event listeners
    list.querySelectorAll('.btn-remove').forEach(btn => {
        btn.addEventListener('click', async () => {
            const idx = parseInt(btn.dataset.index);
            await removeVideoFromInspection(idx);
        });
    });

    // Update video count
    await refreshStatus();

    // Hide inspection section if no videos left
    if (validationResult.valid_videos.length === 0) {
        document.getElementById('video-inspection-section').style.display = 'none';
    }
}

function closeInspection() {
    document.getElementById('video-inspection-section').style.display = 'none';
}

async function startProcessingFromWelcome() {
    const btn = document.getElementById('btn-start-processing');
    btn.disabled = true;
    btn.textContent = 'Starting...';

    // Get segmentation and overlap checkboxes
    const segmentationEnabled = document.getElementById('segmentation-enabled').checked;
    const overlapEnabled = document.getElementById('overlap-enabled').checked;

    // Always pause for transcription review (segment_only=true)
    // Segmentation setting controls whether videos are split or kept whole
    const result = await api('start', 'POST', {
        train_kmeans: false,  // Not needed for initial processing
        golden_model: null,
        segmentation_enabled: segmentationEnabled,
        overlap_enabled: overlapEnabled,
        segment_only: true  // Always pause for transcription review
    });

    if (!result.success) {
        alert(`Failed to start: ${result.errors?.join(', ') || result.message}`);
        btn.disabled = false;
        btn.textContent = 'Start Processing';
        return;
    }

    showScreen('processing');
    startProgressPolling();
}

// Segment Review Screen
async function loadAndDisplaySegments() {
    try {
        console.log('Loading segments...');

        // Load segments
        const segmentsData = await api('segments', 'GET');
        console.log('Segments data:', segmentsData);

        if (segmentsData.error) {
            alert(`Failed to load segments: ${segmentsData.error}`);
            showScreen('welcome');
            return;
        }

        // Load orphaned transcriptions
        const orphanedData = await api('orphaned-transcriptions');
        const orphanedTranscriptions = orphanedData.orphaned || [];
        console.log('Orphaned transcriptions:', orphanedTranscriptions);

        // Display segments
        console.log('Displaying segment review...');
        displaySegmentReview(segmentsData, orphanedTranscriptions);

        // Show segment review screen
        console.log('Showing segment review screen');
        showScreen('segmentReview');

    } catch (err) {
        console.error('Failed to load segments:', err);
        alert('Failed to load segments. Returning to welcome screen.');
        showScreen('welcome');
    }
}

async function continueFullPipeline() {
    const btn = document.getElementById('btn-continue-pipeline');
    if (!btn) return;

    // A1 audit: try/finally guarantees the button never stays stuck on
    // "Starting...". A thrown error or unexpected api() response would
    // previously leave the user with a frozen button.
    btn.disabled = true;
    btn.textContent = 'Starting...';
    let started = false;

    try {
        const kmeansMode = document.querySelector('#segment-review-screen input[name="kmeans-mode"]:checked')?.value;
        let trainKmeans = false;
        let goldenModel = null;

        if (kmeansMode === 'train') {
            trainKmeans = true;
        } else if (kmeansMode === 'golden') {
            const goldenSelect = document.querySelector('#segment-review-screen #golden-model-select');
            goldenModel = goldenSelect?.value;

            if (!goldenModel) {
                alert('Please select a golden model or choose a different option');
                return;
            }
        }

        const segmentationEnabled = document.getElementById('segmentation-enabled')?.checked ?? true;
        const overlapEnabled = document.getElementById('overlap-enabled')?.checked ?? true;

        const result = await api('start', 'POST', {
            train_kmeans: trainKmeans,
            golden_model: goldenModel,
            segmentation_enabled: segmentationEnabled,
            overlap_enabled: overlapEnabled,
            segment_only: false
        });

        if (!result.success) {
            alert(`Failed to start: ${result.errors?.join(', ') || result.message || result.error || 'Unknown error'}`);
            return;
        }

        started = true;
        showScreen('processing');
        startProgressPolling();
    } catch (err) {
        console.warn('[A1 audit] continueFullPipeline threw:', err);
        alert(`Failed to start: ${err?.message || err}`);
    } finally {
        if (!started) {
            btn.disabled = false;
            btn.textContent = 'Continue Pipeline';
        }
    }
}

function displaySegmentReview(segmentsData, orphanedTranscriptionsParam) {
    const segments = segmentsData.segments || [];
    const transcribed = segmentsData.transcribed || 0;
    const total = segmentsData.total || 0;

    // Update stats
    document.getElementById('segment-count').textContent = total;
    document.getElementById('transcribed-count').textContent = transcribed;

    // Calculate total duration
    const totalDuration = segments.reduce((sum, s) => sum + (s.duration || 0), 0);
    document.getElementById('total-duration').textContent = formatDuration(totalDuration);

    // Display segments list
    const segmentsList = document.getElementById('segments-list');
    segmentsList.innerHTML = segments
        .map(s => `
            <li>
                <div class="video-list-item">
                    <div class="video-info">
                        <span class="video-name">${escapeHtml(s.filename)}</span>
                        <span class="video-duration">${formatDuration(s.duration)}</span>
                        ${s.has_transcription
                            ? `<span class="badge-${s.transcription_type || 'auto'}">[${(s.transcription_type || 'auto').toUpperCase()}]</span>`
                            : '<span class="badge-none">[NO TRANSCRIPTION]</span>'}
                    </div>
                    <div class="video-actions">
                        <button class="btn-transcription"
                                data-filename="${escapeHtml(s.id)}.mp4"
                                data-segment-id="${escapeHtml(s.id)}"
                                data-has-transcription="${s.has_transcription || false}"
                                data-type="${s.transcription_type || ''}">
                            ${s.has_transcription ? 'Edit' : 'Add'} Transcription
                        </button>
                        ${s.has_transcription
                            ? `<button class="btn-delete-transcription"
                                       data-filename="${escapeHtml(s.id)}.mp4"
                                       data-type="${s.transcription_type || ''}"
                                       title="Delete transcription">Delete</button>`
                            : ''}
                    </div>
                </div>
            </li>
        `)
        .join('');

    // Add event listeners for transcription buttons
    segmentsList.querySelectorAll('.btn-transcription').forEach(btn => {
        btn.addEventListener('click', () => {
            const filename = btn.dataset.filename;
            const segmentId = btn.dataset.segmentId;
            const type = btn.dataset.type || null;
            openTranscriptionModal(filename, btn.dataset.hasTranscription === 'true', type, segmentId);
        });
    });

    segmentsList.querySelectorAll('.btn-delete-transcription').forEach(btn => {
        btn.addEventListener('click', () => deleteTranscriptionFromList(btn.dataset.filename, btn.dataset.type));
    });

    // Display orphaned transcriptions (set global variable for delete/keep functions)
    orphanedTranscriptions = orphanedTranscriptionsParam;
    displayOrphanedTranscriptions();

    // Load golden k-means models for segment review screen
    loadGoldenModels();
}

// Validation Screen (Legacy - Remove)
async function scanVideos() {
    const btn = document.getElementById('btn-scan');
    btn.disabled = true;
    btn.textContent = 'Scanning...';

    try {
        validationResult = await api('validate', 'POST');

        if (validationResult.error) {
            alert(`Validation error: ${validationResult.error}`);
            return;
        }

        displayValidationResults();
        showScreen('validation');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Scan Videos';
    }
}

function displayValidationResults() {
    const result = validationResult;

    // Stats
    elements.validCount.textContent = result.valid_videos.length;
    elements.segmentCount.textContent = result.total_segments;
    elements.totalDuration.textContent = formatDuration(result.total_duration_seconds);

    // Update overlap label with dynamic min_split_duration
    const overlapLabel = document.getElementById('overlap-label-text');
    if (overlapLabel && result.min_split_duration) {
        overlapLabel.textContent = `Enable overlapping segments for videos >${result.min_split_duration}s`;
    }

    // Warnings
    if (result.warnings.length > 0) {
        elements.warningsContainer.style.display = 'block';
        elements.warningsList.innerHTML = result.warnings
            .map(w => `<li>${escapeHtml(w)}</li>`)
            .join('');
    } else {
        elements.warningsContainer.style.display = 'none';
    }

    // Valid videos with transcription buttons and remove buttons
    elements.validVideosList.innerHTML = result.valid_videos
        .map((v, index) => `
            <li>
                <div class="video-list-item">
                    <div class="video-info">
                        <span class="video-name">${escapeHtml(v.filename)}</span>
                        <span class="video-duration">${formatDuration(v.duration_seconds)}</span>
                        ${v.has_transcription
                            ? `<span class="badge-${v.transcription_type}">[${v.transcription_type.toUpperCase()}]</span>`
                            : ''}
                    </div>
                    <div class="video-actions">
                        <button class="btn-remove" data-index="${index}">Remove</button>
                    </div>
                </div>
            </li>
        `)
        .join('');

    // Add event listeners to remove buttons
    document.querySelectorAll('.btn-remove').forEach(btn => {
        btn.addEventListener('click', () => removeVideo(parseInt(btn.dataset.index)));
    });

    // Invalid videos
    if (result.invalid_videos.length > 0) {
        elements.invalidVideosSection.style.display = 'block';
        elements.invalidVideosList.innerHTML = result.invalid_videos
            .map(v => `
                <li>
                    <div>
                        <span class="video-name">${escapeHtml(v.filename)}</span>
                        <div class="video-error">${escapeHtml(v.error)}</div>
                    </div>
                </li>
            `)
            .join('');
    } else {
        elements.invalidVideosSection.style.display = 'none';
    }

    // Existing segments (from previous runs)
    const existingSegmentsSection = document.getElementById('existing-segments-section');
    const existingSegmentsList = document.getElementById('existing-segments-list');

    if (result.existing_segments && result.existing_segments.length > 0) {
        existingSegmentsSection.style.display = 'block';
        existingSegmentsList.innerHTML = result.existing_segments
            .map(s => `
                <li>
                    <div class="video-list-item">
                        <div class="video-info">
                            <span class="video-name">${escapeHtml(s.filename)}</span>
                            <span class="video-duration">${formatDuration(s.duration)}</span>
                            ${s.has_transcription
                                ? `<span class="badge-${s.transcription_type}">[${s.transcription_type.toUpperCase()}]</span>`
                                : '<span class="badge-none">[NO TRANSCRIPTION]</span>'}
                        </div>
                        <div class="video-actions">
                            <button class="btn-transcription"
                                    data-filename="${escapeHtml(s.id)}.mp4"
                                    data-has-transcription="${s.has_transcription || false}"
                                    data-type="${s.transcription_type || ''}">
                                ${s.has_transcription ? 'Edit' : 'Add'} Transcription
                            </button>
                            ${s.has_transcription
                                ? `<button class="btn-delete-transcription"
                                           data-filename="${escapeHtml(s.id)}.mp4"
                                           data-type="${s.transcription_type || ''}"
                                           title="Delete transcription">Delete</button>`
                                : ''}
                        </div>
                    </div>
                </li>
            `)
            .join('');

        // Add event listeners for segment transcription buttons
        existingSegmentsList.querySelectorAll('.btn-transcription').forEach(btn => {
            btn.addEventListener('click', () => {
                const filename = btn.dataset.filename;
                const type = btn.dataset.type || null;
                openTranscriptionModal(filename, btn.dataset.hasTranscription === 'true', type);
            });
        });

        existingSegmentsList.querySelectorAll('.btn-delete-transcription').forEach(btn => {
            btn.addEventListener('click', () => deleteTranscriptionFromList(btn.dataset.filename, btn.dataset.type));
        });
    } else {
        existingSegmentsSection.style.display = 'none';
    }

    // Enable/disable start button
    const startBtn = document.getElementById('btn-start');
    startBtn.disabled = result.valid_videos.length === 0;

    // Load golden k-means models
    loadGoldenModels();

    // Load orphaned transcriptions
    loadOrphanedTranscriptions();
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

async function removeVideo(index) {
    if (!validationResult) return;

    const video = validationResult.valid_videos[index];

    // Confirm removal
    if (!confirm(`Remove "${video.filename}"?`)) {
        return;
    }

    // Call API to delete the file
    const result = await api('remove-video', 'POST', { filename: video.filename });

    if (!result.success) {
        alert(`Failed to remove video: ${result.error || 'Unknown error'}`);
        return;
    }

    // Remove video from valid list
    validationResult.valid_videos.splice(index, 1);

    // Recalculate totals
    validationResult.total_duration_seconds -= video.duration_seconds;
    validationResult.total_segments -= video.segments;

    // Re-check k-means warning
    validationResult.warnings = validationResult.warnings.filter(w => !w.includes('k-means'));
    if (validationResult.total_segments < 200) {
        validationResult.warnings.push(
            `Only ${validationResult.total_segments} segments (minimum 200 recommended for k-means training). ` +
            `You can proceed but results may be suboptimal.`
        );
    }

    // Refresh display
    displayValidationResults();
}

// Transcription Management
let currentSegmentId = null;

async function openTranscriptionModal(filename, hasTranscription, type, segmentId = null) {
    currentTranscriptionFilename = filename;
    currentTranscriptionType = type;
    currentSegmentId = segmentId;

    // Set filename in modal
    document.getElementById('transcription-video-name').textContent = filename;

    // Reset video container (don't auto-load)
    const videoContainer = document.getElementById('transcription-video-container');
    videoContainer.style.display = 'none';
    videoContainer.innerHTML = '';

    // Show/hide the "Show Video" button based on whether we have a segment
    const showVideoBtn = document.getElementById('show-video-btn');
    if (segmentId) {
        showVideoBtn.style.display = 'inline-block';
        showVideoBtn.textContent = 'Show Video';
        showVideoBtn.dataset.videoLoaded = 'false';
    } else {
        showVideoBtn.style.display = 'none';
    }

    // Load existing transcription if present
    try {
        const result = await api(`transcription?filename=${encodeURIComponent(filename)}`);
        const textarea = document.getElementById('transcription-text');

        if (result.text) {
            textarea.value = result.text;
            document.getElementById('delete-transcription-btn').style.display = 'inline-block';

            // Show type badge and metadata
            const badge = document.getElementById('modal-badge');
            badge.textContent = `[${result.type.toUpperCase()}]`;
            badge.className = `badge-${result.type}`;
            badge.style.display = 'inline-block';

            // Show creation date
            const meta = document.getElementById('transcription-meta');
            const date = result.created_at ? new Date(result.created_at).toLocaleDateString() : 'Unknown';
            const wordCount = result.word_count || 0;
            meta.textContent = ` • Created: ${date} • ${wordCount} words`;
        } else {
            textarea.value = '';
            document.getElementById('delete-transcription-btn').style.display = 'none';
            document.getElementById('modal-badge').style.display = 'none';
            document.getElementById('transcription-meta').textContent = '';
        }

        // Update preview
        updateTranscriptionPreview();
    } catch (err) {
        alert(`Failed to load transcription: ${err.message}`);
        return;
    }

    // Show modal
    document.getElementById('transcription-modal').style.display = 'flex';

    // Focus textarea
    document.getElementById('transcription-text').focus();
}

function toggleVideo() {
    const videoContainer = document.getElementById('transcription-video-container');
    const showVideoBtn = document.getElementById('show-video-btn');
    const isLoaded = showVideoBtn.dataset.videoLoaded === 'true';

    if (isLoaded) {
        // Hide video
        videoContainer.style.display = 'none';
        videoContainer.innerHTML = '';
        showVideoBtn.textContent = 'Show Video';
        showVideoBtn.dataset.videoLoaded = 'false';
    } else {
        // Load and show video
        if (currentSegmentId) {
            videoContainer.style.display = 'block';
            videoContainer.innerHTML = `
                <video controls style="width: 100%; max-height: 400px; margin-bottom: 16px;">
                    <source src="/api/segment-video/${currentSegmentId}" type="video/mp4">
                    Your browser does not support video playback.
                </video>
            `;
            showVideoBtn.textContent = 'Hide Video';
            showVideoBtn.dataset.videoLoaded = 'true';
        }
    }
}

function closeTranscriptionModal() {
    document.getElementById('transcription-modal').style.display = 'none';
    document.getElementById('transcription-text').value = '';
    document.getElementById('transcription-preview').style.display = 'none';
    document.getElementById('modal-badge').style.display = 'none';

    // Reset video state
    const videoContainer = document.getElementById('transcription-video-container');
    videoContainer.style.display = 'none';
    videoContainer.innerHTML = '';

    const showVideoBtn = document.getElementById('show-video-btn');
    if (showVideoBtn) {
        showVideoBtn.dataset.videoLoaded = 'false';
    }

    currentTranscriptionFilename = null;
    currentTranscriptionType = null;
    currentSegmentId = null;
}

function updateTranscriptionPreview() {
    const textarea = document.getElementById('transcription-text');
    const text = textarea.value.trim();

    if (!text) {
        document.getElementById('transcription-preview').style.display = 'none';
        return;
    }

    // Simulate normalization (matches backend logic)
    const words = text
        .toLowerCase()
        .split(/\s+/)
        .map(w => w.replace(/[^a-z0-9']/g, ''))
        .filter(w => w.length > 0);

    document.getElementById('transcription-preview-text').textContent =
        words.join('\n');
    document.getElementById('transcription-preview').style.display = 'block';
}

async function saveTranscription() {
    const text = document.getElementById('transcription-text').value.trim();

    if (!text) {
        alert('Please enter a transcription');
        return;
    }

    try {
        // If editing an [Auto] transcription, it becomes [Manual]
        let type = 'manual';
        if (currentTranscriptionType === 'auto') {
            // Warn user that editing will change it to manual
            if (!confirm('Editing this auto-generated transcription will mark it as [Manual]. Continue?')) {
                return;
            }
        }

        const result = await api('transcription', 'POST', {
            filename: currentTranscriptionFilename,
            text: text,
            type: type
        });

        if (!result.success) {
            alert(`Failed to save: ${result.error || 'Unknown error'}`);
            return;
        }

        // Close modal first
        closeTranscriptionModal();

        // Refresh the current screen - check which screen we're on
        if (currentScreen === 'segmentReview') {
            // Reload segments to show updated transcription
            await loadAndDisplaySegments();
        } else if (validationResult) {
            // Update validation results if we're on validation screen
            const video = validationResult.valid_videos.find(
                v => v.filename === currentTranscriptionFilename
            );
            if (video) {
                video.has_transcription = true;
                video.transcription_type = result.type;
            }
            displayValidationResults();
        }

    } catch (err) {
        alert(`Failed to save: ${err.message}`);
    }
}

async function deleteCurrentTranscription() {
    const typeText = currentTranscriptionType === 'auto' ? 'auto-generated' : 'manual';

    if (!confirm(
        `Delete ${typeText} transcription for "${currentTranscriptionFilename}"?\n\n` +
        `The video will use Whisper ASR on the next pipeline run.`
    )) {
        return;
    }

    try {
        const result = await api('transcription', 'POST', {
            filename: currentTranscriptionFilename,
            delete: true
        });

        if (!result.success) {
            alert(`Failed to delete: ${result.error || 'Unknown error'}`);
            return;
        }

        // Close modal first
        closeTranscriptionModal();

        // Refresh the current screen - check which screen we're on
        if (currentScreen === 'segmentReview') {
            await loadAndDisplaySegments();
        } else if (validationResult) {
            const video = validationResult.valid_videos.find(
                v => v.filename === currentTranscriptionFilename
            );
            if (video) {
                video.has_transcription = false;
                video.transcription_type = null;
            }
            displayValidationResults();
        }

    } catch (err) {
        alert(`Failed to delete: ${err.message}`);
    }
}

async function deleteTranscriptionFromList(filename, type) {
    const typeText = type === 'auto' ? 'auto-generated' : 'manual';

    if (!confirm(
        `Delete ${typeText} transcription for "${filename}"?\n\n` +
        `The video will use Whisper ASR on the next pipeline run.`
    )) {
        return;
    }

    try {
        const result = await api('transcription', 'POST', {
            filename: filename,
            delete: true
        });

        if (!result.success) {
            alert(`Failed to delete: ${result.error || 'Unknown error'}`);
            return;
        }

        // Refresh the current screen - check which screen we're on
        if (currentScreen === 'segmentReview') {
            // Reload segments to show updated transcription
            await loadAndDisplaySegments();
        } else if (validationResult) {
            // Update validation results if we're on validation screen
            const video = validationResult.valid_videos.find(v => v.filename === filename);
            if (video) {
                video.has_transcription = false;
                video.transcription_type = null;
            }
            displayValidationResults();
        }

    } catch (err) {
        alert(`Failed to delete: ${err.message}`);
    }
}

async function loadOrphanedTranscriptions() {
    try {
        const result = await api('orphaned-transcriptions');
        orphanedTranscriptions = result.orphaned || [];

        displayOrphanedTranscriptions();
    } catch (err) {
        console.error('Failed to load orphaned transcriptions:', err);
    }
}

function displayOrphanedTranscriptions() {
    const section = document.getElementById('orphaned-section');
    const list = document.getElementById('orphaned-list');

    if (orphanedTranscriptions.length === 0) {
        section.style.display = 'none';
        return;
    }

    section.style.display = 'block';

    list.innerHTML = orphanedTranscriptions.map((o, index) => {
        const date = o.created_at ? new Date(o.created_at).toLocaleDateString() : 'Unknown';
        const wordCount = o.word_count || 0;
        return `
            <li>
                <div class="orphaned-item">
                    <div class="orphaned-info">
                        <span class="video-name">${escapeHtml(o.filename)}</span>
                        <span class="badge-${o.type}">[${o.type.toUpperCase()}]</span>
                        <span class="orphaned-meta">Created: ${date} • ${wordCount} words</span>
                    </div>
                    <div class="orphaned-actions">
                        <button class="btn btn-secondary btn-sm" onclick="keepOrphan(${index})">
                            Keep
                        </button>
                        <button class="btn btn-danger btn-sm" onclick="deleteOrphan(${index})">
                            Delete
                        </button>
                    </div>
                </div>
            </li>
        `;
    }).join('');
}

async function deleteOrphan(index) {
    const orphan = orphanedTranscriptions[index];

    if (!confirm(`Delete transcription for "${orphan.filename}"?\n\nThis cannot be undone.`)) {
        return;
    }

    try {
        const result = await api('transcription', 'POST', {
            filename: orphan.filename,
            delete: true
        });

        if (!result.success) {
            alert(`Failed to delete: ${result.error || 'Unknown error'}`);
            return;
        }

        // Remove from list and refresh
        orphanedTranscriptions.splice(index, 1);
        displayOrphanedTranscriptions();

    } catch (err) {
        alert(`Failed to delete: ${err.message}`);
    }
}

function keepOrphan(index) {
    // Just dismiss - user wants to keep it
    // Remove from display but don't delete the file
    orphanedTranscriptions.splice(index, 1);
    displayOrphanedTranscriptions();
}

// Processing Screen
async function loadGoldenModels() {
    const goldenSelect = document.getElementById('golden-model-select');

    try {
        const response = await api('golden-models', 'GET');
        const models = response.models || [];

        if (models.length === 0) {
            goldenSelect.innerHTML = '<option value="">No golden models available</option>';
            goldenSelect.disabled = true;
        } else {
            goldenSelect.innerHTML = models
                .map(m => {
                    const sizeMB = (m.size / (1024 * 1024)).toFixed(2);
                    return `<option value="${m.path}">${m.name} (${sizeMB} MB)</option>`;
                })
                .join('');
            goldenSelect.disabled = false;
        }
    } catch (error) {
        console.error('Failed to load golden models:', error);
        goldenSelect.innerHTML = '<option value="">Error loading models</option>';
        goldenSelect.disabled = true;
    }
}

async function startProcessing() {
    const btn = document.getElementById('btn-start');
    btn.disabled = true;

    // Get k-means mode
    const kmeansMode = document.querySelector('input[name="kmeans-mode"]:checked').value;

    let trainKmeans = false;
    let goldenModel = null;

    if (kmeansMode === 'train') {
        trainKmeans = true;
    } else if (kmeansMode === 'golden') {
        const goldenSelect = document.getElementById('golden-model-select');
        goldenModel = goldenSelect.value;

        if (!goldenModel) {
            alert('Please select a golden model or choose a different option');
            btn.disabled = false;
            return;
        }
    }
    // else kmeansMode === 'existing': trainKmeans=false, goldenModel=null

    // Get segmentation and overlap checkboxes
    const segmentationEnabled = document.getElementById('segmentation-enabled').checked;
    const overlapEnabled = document.getElementById('overlap-enabled').checked;

    // Get manual transcription checkbox
    const manualTranscription = document.getElementById('manual-transcription').checked;

    const result = await api('start', 'POST', {
        train_kmeans: trainKmeans,
        golden_model: goldenModel,
        segmentation_enabled: segmentationEnabled,
        overlap_enabled: overlapEnabled,
        segment_only: manualTranscription  // Only pause for transcription if user checked the box
    });

    if (!result.success) {
        alert(`Failed to start: ${result.errors?.join(', ') || result.message}`);
        btn.disabled = false;
        return;
    }

    showScreen('processing');
    startProgressPolling();
}

function startProgressPolling() {
    // Clear any existing interval
    if (pollInterval) {
        clearInterval(pollInterval);
    }

    // Poll every 500ms
    pollInterval = setInterval(updateProgress, 500);

    // Initial update
    updateProgress();
}

function stopProgressPolling() {
    if (pollInterval) {
        clearInterval(pollInterval);
        pollInterval = null;
    }
}

async function updateProgress() {
    const progress = await api('progress');

    if (progress.error) {
        return;
    }

    // Update progress bar
    elements.progressFill.style.width = `${progress.percent_complete}%`;
    elements.progressPercent.textContent = `${progress.percent_complete}%`;

    // Update stage info
    elements.stageName.textContent = progress.current_stage_name || 'Initializing...';
    elements.stageDescription.textContent = progress.current_stage_description || '';

    // Update decode counter (only visible during stage 7, once total is known)
    const showDecodeCounter = progress.current_stage_id === 'decode' && (progress.decode_total || 0) > 0;
    if (elements.decodeCounter) {
        elements.decodeCounter.style.display = showDecodeCounter ? 'block' : 'none';
        if (showDecodeCounter) {
            elements.decodeDone.textContent = progress.decode_done || 0;
            elements.decodeTotal.textContent = progress.decode_total;
        }
    }

    // Update ETA
    // Update logs if visible
    if (logsVisible) {
        await updateLogs();
    }

    // Check for state changes
    if (progress.state === 'completed') {
        stopProgressPolling();

        // Check if this was segment-only mode (fast segmentation)
        if (progress.segment_only) {
            // Load segments and show segment review screen
            await loadAndDisplaySegments();
        } else {
            // Normal completion - show results
            elements.outputPath.textContent = progress.output_path || 'Results folder';
            showScreen('complete');
        }
    } else if (progress.state === 'failed') {
        stopProgressPolling();
        showErrorScreen(progress);
    } else if (progress.state === 'cancelled') {
        stopProgressPolling();
        // Reset backend state after cancellation
        await api('reset', 'POST');
        showScreen('welcome');
        refreshStatus();
    }
}

async function updateLogs() {
    const result = await api('logs?n=100');
    if (result.logs) {
        const logs = Array.isArray(result.logs) ? result.logs.join('\n') : result.logs;
        elements.logsOutput.textContent = logs;

        // Auto-scroll to bottom
        const container = elements.logsContainer;
        container.scrollTop = container.scrollHeight;
    }
}

function toggleLogs() {
    logsVisible = !logsVisible;
    elements.logsContainer.style.display = logsVisible ? 'block' : 'none';
    document.getElementById('btn-toggle-logs').textContent = logsVisible ? 'Hide Logs' : 'Show Logs';

    if (logsVisible) {
        updateLogs();
    }
}

async function cancelProcessing() {
    if (!confirm('Are you sure you want to cancel processing?')) {
        return;
    }

    const btn = document.getElementById('btn-cancel');
    btn.disabled = true;
    btn.textContent = 'Cancelling...';

    await api('cancel', 'POST');

    // Progress polling will handle the state change
}

// Error Screen
function showErrorScreen(progress) {
    const errors = progress.errors || [];
    const lastError = errors[errors.length - 1] || 'Unknown error';

    elements.errorMessage.textContent = `Processing failed at stage: ${progress.current_stage_name || 'Unknown'}`;
    elements.errorDetails.textContent = errors.join('\n') || 'No details available';

    showScreen('error');
}

async function showErrorLogs() {
    const result = await api('logs?all=1');
    if (result.logs) {
        const logs = Array.isArray(result.logs) ? result.logs.join('\n') : result.logs;
        elements.errorLogsOutput.textContent = logs;
        elements.errorLogsContainer.style.display = 'block';
        document.getElementById('btn-show-error-logs').textContent = 'Hide Full Logs';
    }
}

async function retryProcessing() {
    // Reset backend state before retrying
    await api('reset', 'POST');

    // Go back to welcome screen for retry in new workflow
    showScreen('welcome');
    await refreshStatus();
}

// Complete Screen
async function downloadOutput() {
    // Download the output folder as a zip file
    window.location.href = '/api/download-output';
}


async function startNew() {
    validationResult = null;
    logsVisible = false;
    elements.logsContainer.style.display = 'none';
    elements.errorLogsContainer.style.display = 'none';

    // Reset backend state
    await api('reset', 'POST');

    showScreen('welcome');
    refreshStatus();
}

// Drag-and-Drop Upload Functions
// A2 audit (May 2026): the overlay never appeared on the Win 11 client.
// Hardened: try/catch around every check, scoped #status-badge selector,
// console breadcrumbs so we can diagnose if it recurs, and a guaranteed
// file-picker fallback (see #btn-add-files in the welcome screen).

function handleDragOver(e) {
    e.preventDefault();
    e.stopPropagation();

    try {
        if (isUploading) {
            console.warn('[A2] dragover: skipped — isUploading=true');
            return;
        }
        const badge = document.querySelector('#status-badge');
        const isProcessing = !!(badge && badge.classList.contains('running'));
        if (isProcessing) {
            console.warn('[A2] dragover: skipped — pipeline running');
            return;
        }
        if (!elements.dropZoneOverlay) {
            console.warn('[A2] dragover: drop-zone-overlay element missing');
            return;
        }
        elements.dropZoneOverlay.style.display = 'flex';
    } catch (err) {
        console.warn('[A2] dragover handler threw:', err);
    }
}

function handleDragLeave(e) {
    e.preventDefault();
    e.stopPropagation();

    // Only hide if leaving the window, not just moving between elements.
    if (e.target === document.body || e.target === elements.dropZoneOverlay) {
        if (elements.dropZoneOverlay) {
            elements.dropZoneOverlay.style.display = 'none';
        }
    }
}

function handleDrop(e) {
    e.preventDefault();
    e.stopPropagation();

    if (elements.dropZoneOverlay) {
        elements.dropZoneOverlay.style.display = 'none';
    }

    try {
        if (isUploading) {
            console.warn('[A2] drop: blocked — isUploading=true');
            return;
        }
        const files = Array.from(e.dataTransfer?.files || []);
        console.info('[A2] drop: files=', files.length);
        if (files.length > 0) {
            uploadFiles(files);
        }
    } catch (err) {
        console.warn('[A2] drop handler threw:', err);
    }
}

function isValidVideoFile(filename) {
    // Mirror of backend SUPPORTED_EXTENSIONS in vsp-ui/app/config.py.
    // Keep these two lists in sync when adding/removing a format.
    const validExtensions = [
        '.mp4', '.mkv', '.webm', '.mov', '.m4v', '.avi',
        '.mts', '.m2ts', '.ts',
        '.wmv', '.flv',
    ];
    const ext = filename.toLowerCase().match(/\.[^.]+$/);
    return ext && validExtensions.includes(ext[0]);
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    const k = 1024;
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${(bytes / Math.pow(k, i)).toFixed(1)} ${units[i]}`;
}

async function uploadFiles(files) {
    // Filter valid video files
    const videoFiles = files.filter(f => isValidVideoFile(f.name));
    const rejectedCount = files.length - videoFiles.length;

    if (videoFiles.length === 0) {
        alert('No valid video files selected. Supported: MP4, MKV, WebM, MOV, M4V, AVI');
        return;
    }

    if (rejectedCount > 0) {
        alert(`${rejectedCount} file(s) skipped (not video files)`);
    }

    isUploading = true;
    uploadResults = [];

    // Show upload progress section
    elements.uploadProgressSection.style.display = 'block';
    elements.uploadStatus.textContent = `Uploading 0 of ${videoFiles.length} files...`;
    elements.uploadFilesList.innerHTML = '';

    // Create upload items for each file and store file IDs
    const timestamp = Date.now();
    const fileIds = [];

    videoFiles.forEach((file, index) => {
        const fileId = `upload-${timestamp}-${index}`;
        fileIds.push(fileId);
        const itemHtml = `
            <div class="upload-file-item" data-file-id="${fileId}">
                <div class="upload-file-info">
                    <span class="upload-file-name">${escapeHtml(file.name)}</span>
                    <span class="upload-file-size">${formatFileSize(file.size)}</span>
                </div>
                <div class="upload-file-progress">
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: 0%"></div>
                    </div>
                    <span class="progress-percent">0%</span>
                </div>
                <span class="upload-file-status"></span>
            </div>
        `;
        elements.uploadFilesList.insertAdjacentHTML('beforeend', itemHtml);
    });

    // Upload files in parallel using the stored file IDs
    const uploadPromises = videoFiles.map((file, index) => {
        return uploadFile(file, fileIds[index]);
    });

    // Wait for all uploads to complete
    const results = await Promise.all(uploadPromises);
    uploadResults = results;

    // Update status
    const successCount = results.filter(r => r.success).length;
    const failCount = results.filter(r => !r.success).length;

    elements.uploadStatus.textContent = `Complete: ${successCount} uploaded, ${failCount} failed`;

    // Refresh video count
    // A2 audit: clear isUploading IMMEDIATELY so the user can drop again
    // without waiting 3s. The 3s timer is only for hiding the visual block,
    // not for gating drops.
    isUploading = false;
    await refreshStatus();

    // Hide upload progress after 3 seconds (visual delay only).
    setTimeout(() => {
        elements.uploadProgressSection.style.display = 'none';
    }, 3000);
}

function uploadFile(file, fileId) {
    return new Promise((resolve, reject) => {
        const formData = new FormData();
        formData.append('file', file);

        const xhr = new XMLHttpRequest();

        // Progress event
        xhr.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable) {
                const percent = Math.round((e.loaded / e.total) * 100);
                updateUploadProgress(fileId, percent);
            }
        });

        // Load event (success)
        xhr.addEventListener('load', () => {
            if (xhr.status === 200) {
                try {
                    const response = JSON.parse(xhr.responseText);
                    if (response.success) {
                        markUploadComplete(fileId, true);
                        resolve({ success: true, filename: response.filename });
                    } else {
                        markUploadComplete(fileId, false);
                        resolve({ success: false, error: response.error || 'Unknown error' });
                    }
                } catch (e) {
                    markUploadComplete(fileId, false);
                    resolve({ success: false, error: 'Invalid response' });
                }
            } else {
                markUploadComplete(fileId, false);
                resolve({ success: false, error: `HTTP ${xhr.status}` });
            }
        });

        // Error event
        xhr.addEventListener('error', () => {
            markUploadComplete(fileId, false);
            resolve({ success: false, error: 'Network error' });
        });

        // Abort event
        xhr.addEventListener('abort', () => {
            markUploadComplete(fileId, false);
            resolve({ success: false, error: 'Upload cancelled' });
        });

        // Timeout event (5 min base + 1 min per 100MB)
        xhr.addEventListener('timeout', () => {
            markUploadComplete(fileId, false);
            const sizeMB = (fileSize / (1024 * 1024)).toFixed(0);
            resolve({ success: false, error: `Upload timed out (${sizeMB} MB). Try a smaller file or check network.` });
        });

        // Send request
        xhr.open('POST', '/api/upload');
        const fileSize = file.size || 0;
        xhr.timeout = 300000 + Math.ceil(fileSize / (100 * 1024 * 1024)) * 60000;
        xhr.send(formData);
    });
}

function updateUploadProgress(fileId, percent) {
    const item = document.querySelector(`[data-file-id="${fileId}"]`);
    if (!item) return;

    const progressFill = item.querySelector('.progress-fill');
    const progressPercent = item.querySelector('.progress-percent');

    if (progressFill) progressFill.style.width = `${percent}%`;
    if (progressPercent) progressPercent.textContent = `${percent}%`;

    // Update overall status
    const allItems = document.querySelectorAll('.upload-file-item');
    let completedCount = 0;
    allItems.forEach(i => {
        if (i.classList.contains('success') || i.classList.contains('error')) {
            completedCount++;
        }
    });

    elements.uploadStatus.textContent = `Uploading ${completedCount} of ${allItems.length} files...`;
}

function markUploadComplete(fileId, success) {
    const item = document.querySelector(`[data-file-id="${fileId}"]`);
    if (!item) return;

    item.classList.add(success ? 'success' : 'error');

    const status = item.querySelector('.upload-file-status');
    if (status) {
        status.textContent = success ? '✓' : '✗';
    }

    const progressPercent = item.querySelector('.progress-percent');
    if (progressPercent) {
        progressPercent.textContent = success ? '100%' : 'Failed';
    }
}

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    // Drag-and-drop events
    document.addEventListener('dragover', handleDragOver);
    document.addEventListener('dragleave', handleDragLeave);
    document.addEventListener('drop', handleDrop);

    // Welcome screen
    document.getElementById('btn-inspect-videos').addEventListener('click', inspectVideos);
    document.getElementById('btn-close-inspection')?.addEventListener('click', closeInspection);
    document.getElementById('btn-start-processing').addEventListener('click', startProcessingFromWelcome);

    // Segmentation checkbox - show/hide overlap options
    const segmentationCheckbox = document.getElementById('segmentation-enabled');
    const overlapContainer = document.getElementById('overlap-options-container');

    segmentationCheckbox.addEventListener('change', (e) => {
        overlapContainer.style.display = e.target.checked ? 'block' : 'none';
    });

    // Initialize overlap options visibility based on checkbox state
    overlapContainer.style.display = segmentationCheckbox.checked ? 'block' : 'none';

    // Segment review screen — Back must clear backend state first,
    // otherwise refreshStatus() sees state='completed' && segment_only=true
    // and bounces straight back to segment review.
    document.getElementById('btn-back')?.addEventListener('click', async () => {
        await api('reset', 'POST');
        showScreen('welcome');
        await refreshStatus();
    });
    document.getElementById('btn-continue-pipeline')?.addEventListener('click', continueFullPipeline);

    // K-means mode radio buttons - enable/disable golden model select
    document.querySelectorAll('input[name="kmeans-mode"]').forEach(radio => {
        radio.addEventListener('change', (e) => {
            const goldenSelect = document.getElementById('golden-model-select');
            goldenSelect.disabled = e.target.value !== 'golden';
        });
    });

    // Processing screen
    document.getElementById('btn-toggle-logs').addEventListener('click', toggleLogs);
    document.getElementById('btn-cancel').addEventListener('click', cancelProcessing);

    // Complete screen
    document.getElementById('btn-download-output').addEventListener('click', downloadOutput);
    document.getElementById('btn-new').addEventListener('click', startNew);

    // Watch with CC panel
    const btnWatchCc = document.getElementById('btn-watch-cc');
    if (btnWatchCc) btnWatchCc.addEventListener('click', openWatchCcPanel);
    const btnCcClose = document.getElementById('btn-cc-close');
    if (btnCcClose) btnCcClose.addEventListener('click', closeWatchCcPanel);
    const ccSelect = document.getElementById('cc-video-select');
    if (ccSelect) ccSelect.addEventListener('change', () => loadCcVideo(ccSelect.value));
    const ccVideo = document.getElementById('cc-video');
    if (ccVideo) ccVideo.addEventListener('timeupdate', renderCcCaption);

    // Inject-from-audio modal
    const btnInjectAudio = document.getElementById('btn-inject-audio');
    if (btnInjectAudio) btnInjectAudio.addEventListener('click', openInjectAudioModal);

    // Error screen
    document.getElementById('btn-show-error-logs').addEventListener('click', showErrorLogs);
    document.getElementById('btn-retry').addEventListener('click', retryProcessing);
    document.getElementById('btn-back-to-start').addEventListener('click', startNew);

    // Transcription modal
    document.getElementById('transcription-text').addEventListener('input', updateTranscriptionPreview);

    // Close modal on Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && document.getElementById('transcription-modal').style.display === 'flex') {
            closeTranscriptionModal();
        }
    });

    // Close modal on backdrop click
    document.getElementById('transcription-modal').addEventListener('click', (e) => {
        if (e.target.id === 'transcription-modal') {
            closeTranscriptionModal();
        }
    });

    // Copy host input path to clipboard (so the client can paste it into
    // File Explorer instead of memorising %USERPROFILE%\vsp-input).
    const copyPathHandler = async () => {
        const path = elements.inputPath?.textContent?.trim();
        if (!path || path === 'Loading...') return;
        try {
            await navigator.clipboard.writeText(path);
            const btn = document.getElementById('btn-copy-path');
            if (btn) {
                const old = btn.textContent;
                btn.textContent = 'Copied!';
                setTimeout(() => { btn.textContent = old; }, 1500);
            }
        } catch (e) {
            const range = document.createRange();
            range.selectNode(elements.inputPath);
            window.getSelection().removeAllRanges();
            window.getSelection().addRange(range);
        }
    };
    document.getElementById('btn-copy-path')?.addEventListener('click', copyPathHandler);
    elements.inputPath?.addEventListener('click', copyPathHandler);

    // A2 file-picker fallback. Guaranteed to work even when native drag-drop
    // is broken (Edge late-2025 regression, Docker Desktop NAT quirks, etc.).
    const filePicker = document.getElementById('file-picker-input');
    document.getElementById('btn-add-files')?.addEventListener('click', () => {
        filePicker?.click();
    });
    filePicker?.addEventListener('change', (e) => {
        const files = Array.from(e.target.files || []);
        console.info('[A2] file-picker: files=', files.length);
        if (files.length > 0) {
            uploadFiles(files);
        }
        // Reset so the same file can be re-picked.
        e.target.value = '';
    });

    // Archived videos: open/close and restore handlers.
    document.getElementById('btn-toggle-archived')?.addEventListener('click', async () => {
        const section = document.getElementById('archived-section');
        if (!section) return;
        section.style.display = 'block';
        document.getElementById('btn-toggle-archived').style.display = 'none';
        await loadArchivedVideos();
    });
    document.getElementById('btn-close-archived')?.addEventListener('click', () => {
        const section = document.getElementById('archived-section');
        if (section) section.style.display = 'none';
        const btn = document.getElementById('btn-toggle-archived');
        if (btn) btn.style.display = 'inline-block';
    });

    // Initial status check
    refreshStatus();
});

async function loadArchivedVideos() {
    const list = document.getElementById('archived-videos-list');
    if (!list) return;
    list.innerHTML = '<li>Loading…</li>';
    const result = await api('list-archived');
    const files = result.archived || [];
    if (files.length === 0) {
        list.innerHTML = '<li>No archived videos.</li>';
        return;
    }
    list.innerHTML = files
        .map(f => `
            <li>
                <div class="video-list-item">
                    <div class="video-info">
                        <span class="video-name">${escapeHtml(f)}</span>
                    </div>
                    <div class="video-actions">
                        <button class="btn-restore-archived" data-filename="${escapeHtml(f)}">Restore</button>
                    </div>
                </div>
            </li>
        `)
        .join('');
    list.querySelectorAll('.btn-restore-archived').forEach(btn => {
        btn.addEventListener('click', async () => {
            const filename = btn.dataset.filename;
            btn.disabled = true;
            btn.textContent = 'Restoring…';
            const r = await api('restore-video', 'POST', { filename });
            if (!r.success) {
                alert(`Failed to restore: ${r.error || 'Unknown error'}`);
                btn.disabled = false;
                btn.textContent = 'Restore';
                return;
            }
            await loadArchivedVideos();
            await refreshStatus();
        });
    });
}

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    stopProgressPolling();
});

// ============================================================================
// Segment Transcription Functions
// ============================================================================

let currentSegments = [];

async function loadSegments() {
    const result = await api('segments', 'GET');
    if (result.segments) {
        currentSegments = result.segments;
        displaySegments(result.segments, result.transcribed, result.total);
    }
}

function displaySegments(segments, transcribed, total) {
    const segmentList = document.getElementById('segment-list');
    const progressSpan = document.getElementById('transcription-progress');
    const continueBtn = document.getElementById('btn-save-transcriptions');

    progressSpan.textContent = `${transcribed} of ${total} segments transcribed`;

    // Enable button immediately - confirmation dialog handles incomplete transcriptions
    if (total > 0) {
        continueBtn.disabled = false;
    }

    segmentList.innerHTML = '';

    segments.forEach((segment, index) => {
        const segmentDiv = document.createElement('div');
        segmentDiv.className = `segment-item ${segment.has_transcription ? 'transcribed' : ''}`;
        segmentDiv.innerHTML = `
            <div class="segment-header">
                <div class="segment-info">
                    <div class="segment-title">Segment ${index + 1}: ${segment.id}</div>
                    <div class="segment-meta">Duration: ${segment.duration.toFixed(1)}s</div>
                </div>
                <div class="segment-status ${segment.has_transcription ? 'transcribed' : 'pending'}">
                    ${segment.has_transcription ? '✓ Transcribed' : '✗ Pending'}
                </div>
            </div>
            <div class="segment-video">
                <video controls data-segment-id="${segment.id}" data-lazy="true">
                    <source data-src="/api/segment-video/${segment.id}" type="video/mp4">
                    Your browser does not support video playback.
                </video>
                <div class="video-loading" style="display: none; text-align: center; padding: 20px; color: #666;">
                    Loading video...
                </div>
            </div>
            <div class="segment-transcription">
                <label for="transcription-${segment.id}">Transcription:</label>
                <textarea id="transcription-${segment.id}"
                          class="${segment.transcription ? 'has-content' : ''}"
                          placeholder="Type transcription here (space or newline separated words)..."
                          rows="3">${segment.transcription}</textarea>
                <div class="transcription-hint">
                    Text will be normalized: lowercase, alphanumeric + apostrophes only
                </div>
                <div class="transcription-preview" id="preview-${segment.id}" style="display: none;"></div>
                <div class="transcription-word-count" id="count-${segment.id}">
                    ${segment.transcription ? segment.transcription.split(' ').length + ' words' : ''}
                </div>
            </div>
        `;

        // Add event listener for transcription textarea
        const textarea = segmentDiv.querySelector(`#transcription-${segment.id}`);
        textarea.addEventListener('input', () => handleTranscriptionInput(segment.id));
        textarea.addEventListener('blur', () => saveSegmentTranscription(segment.id));

        segmentList.appendChild(segmentDiv);
    });

    // Set up lazy loading for videos using Intersection Observer
    setupVideoLazyLoading();
}

function setupVideoLazyLoading() {
    const lazyVideos = document.querySelectorAll('video[data-lazy="true"]');

    if ('IntersectionObserver' in window) {
        const videoObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const video = entry.target;
                    const source = video.querySelector('source');
                    const dataSrc = source.getAttribute('data-src');

                    if (dataSrc && !source.getAttribute('src')) {
                        // Show loading indicator
                        const loadingDiv = video.nextElementSibling;
                        if (loadingDiv && loadingDiv.classList.contains('video-loading')) {
                            loadingDiv.style.display = 'block';
                            video.style.display = 'none';
                        }

                        // Set the src to trigger video load
                        source.setAttribute('src', dataSrc);
                        video.load();

                        // A1 audit: 30-second timeout. The /api/segment-video/<id>
                        // endpoint runs ffmpeg on demand; it can hang in some
                        // conditions (locked source file, codec quirk). Without
                        // this, the page shows "Loading video..." forever and
                        // looks frozen to the user.
                        const timeoutId = setTimeout(() => {
                            if (loadingDiv && loadingDiv.style.display !== 'none') {
                                console.warn('[A1 audit] video load timed out:', dataSrc);
                                loadingDiv.innerHTML =
                                    '<button class="btn btn-text" title="Retry loading this segment">[Click to retry]</button>';
                                loadingDiv.querySelector('button')?.addEventListener('click', () => {
                                    loadingDiv.textContent = 'Loading video...';
                                    source.setAttribute('src', '');
                                    source.setAttribute('src', dataSrc + '?retry=' + Date.now());
                                    video.load();
                                });
                            }
                        }, 30000);

                        // Hide loading indicator when video can play
                        video.addEventListener('loadeddata', () => {
                            clearTimeout(timeoutId);
                            if (loadingDiv) {
                                loadingDiv.style.display = 'none';
                                video.style.display = 'block';
                            }
                        }, { once: true });

                        // Remove lazy attribute
                        video.removeAttribute('data-lazy');

                        // Stop observing this video
                        observer.unobserve(video);
                    }
                }
            });
        }, {
            rootMargin: '200px' // Start loading 200px before video comes into view
        });

        lazyVideos.forEach(video => {
            videoObserver.observe(video);
        });
    } else {
        // Fallback for browsers without Intersection Observer
        lazyVideos.forEach(video => {
            const source = video.querySelector('source');
            source.setAttribute('src', source.getAttribute('data-src'));
            video.load();
        });
    }
}

function handleTranscriptionInput(segmentId) {
    const textarea = document.getElementById(`transcription-${segmentId}`);
    const preview = document.getElementById(`preview-${segmentId}`);
    const wordCount = document.getElementById(`count-${segmentId}`);

    const text = textarea.value.trim();

    if (text) {
        textarea.classList.add('has-content');

        // Normalize text for preview
        const normalized = text.toLowerCase()
            .replace(/[^a-z0-9'\s]/g, ' ')
            .replace(/\s+/g, ' ')
            .trim();

        const words = normalized.split(' ').filter(w => w);

        preview.style.display = 'block';
        preview.textContent = normalized;
        wordCount.textContent = `${words.length} word${words.length !== 1 ? 's' : ''}`;
    } else {
        textarea.classList.remove('has-content');
        preview.style.display = 'none';
        wordCount.textContent = '';
    }
}

async function saveSegmentTranscription(segmentId) {
    const textarea = document.getElementById(`transcription-${segmentId}`);
    const transcription = textarea.value.trim();

    if (!transcription) {
        return; // Don't save empty transcriptions
    }

    const result = await api('save-segment-transcription', 'POST', {
        segment_id: segmentId,
        transcription: transcription
    });

    if (result.success) {
        // Update segment status
        const segment = currentSegments.find(s => s.id === segmentId);
        if (segment) {
            segment.has_transcription = true;
            segment.transcription = transcription;
        }

        // Refresh display
        const transcribed = currentSegments.filter(s => s.has_transcription).length;
        const total = currentSegments.length;
        const progressSpan = document.getElementById('transcription-progress');
        progressSpan.textContent = `${transcribed} of ${total} segments transcribed`;

        // Enable continue button if all transcribed
        if (transcribed === total) {
            document.getElementById('btn-save-transcriptions').disabled = false;
        }

        // Mark segment as transcribed
        const segmentDiv = textarea.closest('.segment-item');
        segmentDiv.classList.add('transcribed');
        const statusDiv = segmentDiv.querySelector('.segment-status');
        statusDiv.className = 'segment-status transcribed';
        statusDiv.textContent = '✓ Transcribed';
    } else {
        alert(`Failed to save transcription: ${result.message || 'Unknown error'}`);
    }
}

async function continueAfterTranscription() {
    const transcribed = currentSegments.filter(s => s.has_transcription).length;
    const total = currentSegments.length;

    if (transcribed < total) {
        const confirmed = confirm(`Only ${transcribed} of ${total} segments are transcribed. Continue anyway? Untranscribed segments will use automatic ASR.`);
        if (!confirmed) {
            return;
        }
    }

    // Continue pipeline with full processing (normalization, face detection, ASR, etc.)
    const result = await api('start', 'POST', {
        train_kmeans: false, // Don't retrain k-means (use existing or golden)
        overlap_enabled: true,
        segment_only: false // Continue with full processing
    });

    if (result.success) {
        showScreen('processing');
        startProgressPolling();
    } else {
        alert(`Failed to continue pipeline: ${result.message}`);
    }
}

// Event listeners for transcription screen
document.getElementById('btn-save-transcriptions')?.addEventListener('click', continueAfterTranscription);
document.getElementById('btn-cancel-transcription')?.addEventListener('click', () => {
    if (confirm('Cancel transcription? Progress will be saved.')) {
        showScreen('welcome');
    }
});

// =====================================================================
// Watch with CC panel — plays the original (un-segmented) video and
// overlays the per-segment caption coloured by the model's trust band.
// Sidecar: GET /api/whole-video-cc returns {videos: {id: {segments: [...]}}}.
// Video stream: GET /api/original-video/<id>.
// =====================================================================
let ccSidecar = null; // {videos: {...}, _source: "..."}

async function openWatchCcPanel() {
    const panel = document.getElementById('watch-cc-panel');
    const empty = document.getElementById('cc-empty');
    const select = document.getElementById('cc-video-select');
    if (!panel) return;
    panel.style.display = 'block';
    try {
        const resp = await fetch('/api/whole-video-cc');
        if (!resp.ok) {
            ccSidecar = null;
            select.innerHTML = '';
            empty.style.display = 'block';
            return;
        }
        ccSidecar = await resp.json();
    } catch (err) {
        ccSidecar = null;
        select.innerHTML = '';
        empty.style.display = 'block';
        return;
    }
    const ids = Object.keys(ccSidecar.videos || {});
    if (ids.length === 0) {
        empty.style.display = 'block';
        select.innerHTML = '';
        return;
    }
    empty.style.display = 'none';
    select.innerHTML = ids.map(id => `<option value="${id}">${id}</option>`).join('');
    loadCcVideo(ids[0]);
}

function closeWatchCcPanel() {
    const panel = document.getElementById('watch-cc-panel');
    const video = document.getElementById('cc-video');
    if (video) { video.pause(); video.src = ''; }
    if (panel) panel.style.display = 'none';
}

function loadCcVideo(videoId) {
    const video = document.getElementById('cc-video');
    const caption = document.getElementById('cc-caption');
    if (!video) return;
    video.src = `/api/original-video/${encodeURIComponent(videoId)}`;
    video.load();
    if (caption) caption.innerHTML = '';
}

function _activeSegment(videoInfo, t) {
    // Linear scan — segment counts per video are small (tens, not thousands)
    // and the timeupdate fires at ~4Hz so this is well within budget.
    if (!videoInfo) return null;
    for (const seg of videoInfo.segments) {
        if (t >= seg.start_sec && t < seg.end_sec) return seg;
    }
    return null;
}

function renderCcCaption() {
    if (!ccSidecar || !ccSidecar.videos) return;
    const select = document.getElementById('cc-video-select');
    const video = document.getElementById('cc-video');
    const caption = document.getElementById('cc-caption');
    if (!select || !video || !caption) return;
    const info = ccSidecar.videos[select.value];
    const seg = _activeSegment(info, video.currentTime);
    if (!seg) {
        caption.innerHTML = '';
        caption.classList.remove('cc-stripped');
        return;
    }
    const wordsHtml = (seg.words || []).map(w => {
        const klass = w.conf_class || 'conf-unknown';
        const probStr = (typeof w.prob === 'number') ? w.prob.toFixed(2) : 'n/a';
        // Escape word content defensively.
        const txt = (w.word || '').replace(/[&<>"']/g, c => (
            {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]
        ));
        return `<span class="word ${klass}" title="p = ${probStr}">${txt}</span>`;
    }).join(' ');
    if (seg.stripped) {
        caption.classList.add('cc-stripped');
        caption.innerHTML = `<div class="cc-strip-tag">low confidence — coloring stripped</div><div>${wordsHtml}</div>`;
    } else {
        caption.classList.remove('cc-stripped');
        caption.innerHTML = wordsHtml;
    }
}

// =====================================================================
// Audio-aligned transcription injection modal.
// =====================================================================
async function openInjectAudioModal() {
    const modal = document.getElementById('inject-audio-modal');
    const select = document.getElementById('inject-video-select');
    if (!modal || !select) return;
    // Populate the video dropdown from the live INPUT_DIR. Reuse the
    // /api/status path that returns video_count, but we need names —
    // fall back to scanning the segment list which knows parent videos.
    select.innerHTML = '<option>Loading…</option>';
    document.getElementById('inject-status').style.display = 'none';
    document.getElementById('inject-log').style.display = 'none';
    document.getElementById('inject-audio-file').value = '';
    try {
        // /api/segments groups segments by parent video already.
        const resp = await fetch('/api/segments');
        if (!resp.ok) throw new Error('segments endpoint failed');
        const data = await resp.json();
        // Derive parent video filenames from segment IDs. Segment id format:
        //   <video>_NN_NNNNNN_NNNNNN
        const seenParents = new Set();
        for (const s of (data.segments || [])) {
            const stem = (s.id || '').replace(/_(\d{2})_(\d{6})_(\d{6})$/, '');
            if (stem && !seenParents.has(stem)) seenParents.add(stem);
        }
        const parents = Array.from(seenParents).sort();
        if (parents.length === 0) {
            select.innerHTML = '<option value="">(no segmented videos found)</option>';
        } else {
            // Try .mp4 first; the CLI will resolve other extensions too.
            select.innerHTML = parents.map(p => `<option value="${p}.mp4">${p}</option>`).join('');
        }
    } catch (err) {
        select.innerHTML = `<option value="">(error: ${err.message})</option>`;
    }
    modal.style.display = 'flex';
}

function closeInjectAudioModal() {
    document.getElementById('inject-audio-modal').style.display = 'none';
}

async function submitInjectAudio() {
    const videoName = document.getElementById('inject-video-select').value;
    const audioFile = document.getElementById('inject-audio-file').files[0];
    const audioStart = parseFloat(document.getElementById('inject-audio-start').value || '0');
    const videoStart = parseFloat(document.getElementById('inject-video-start').value || '0');
    const whisperModel = document.getElementById('inject-whisper-model').value || 'medium';
    const status = document.getElementById('inject-status');
    const log = document.getElementById('inject-log');
    const btn = document.getElementById('btn-inject-submit');

    if (!videoName) { alert('Please pick a video.'); return; }
    if (!audioFile) { alert('Please choose an audio file.'); return; }

    status.style.display = 'block';
    status.textContent = `Uploading audio and running Whisper on ${whisperModel} model…`;
    log.style.display = 'none';
    btn.disabled = true;
    try {
        const form = new FormData();
        form.append('video', videoName);
        form.append('audio', audioFile, audioFile.name);
        form.append('audio_start', String(audioStart));
        form.append('video_start', String(videoStart));
        form.append('whisper_model', whisperModel);
        const resp = await fetch('/api/inject-from-audio', { method: 'POST', body: form });
        const data = await resp.json();
        if (resp.ok && data.success) {
            status.textContent = `Done — written: ${data.segments_written} · skipped: ${data.segments_skipped} · failed: ${data.segments_failed}`;
        } else {
            status.textContent = `Failed (rc=${data.returncode ?? '—'}): ${data.error || ''}`;
        }
        if (data.log) {
            log.textContent = data.log;
            log.style.display = 'block';
        }
        // Refresh the segment list so freshly-written .wrd files show up
        // with their MANUAL/AUTO badges.
        if (typeof loadAndDisplaySegments === 'function') {
            try { await loadAndDisplaySegments(); } catch (_) { /* non-fatal */ }
        }
    } catch (err) {
        status.textContent = `Error: ${err.message}`;
    } finally {
        btn.disabled = false;
    }
}
