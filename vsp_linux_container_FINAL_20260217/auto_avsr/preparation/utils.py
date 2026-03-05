import os

import torchaudio
import torchvision


def split_file(filename, max_frames=600, fps=25.0):

    lines = open(filename).read().splitlines()

    flag = 0
    stack = []
    res = []

    tmp = 0
    start_timestamp = 0.0

    threshold = max_frames / fps

    for line in lines:
        if "WORD START END ASDSCORE" in line:
            flag = 1
            continue
        if flag:
            word, start, end, score = line.split(" ")
            start, end, score = float(start), float(end), float(score)
            if end < tmp + threshold:
                stack.append(word)
                last_timestamp = end
            else:
                res.append(
                    [
                        " ".join(stack),
                        start_timestamp,
                        last_timestamp,
                        last_timestamp - start_timestamp,
                    ]
                )
                tmp = start
                start_timestamp = start
                stack = [word]
    if stack:
        res.append([" ".join(stack), start_timestamp, end, end - start_timestamp])
    return res


def save_vid_txt(
    dst_vid_filename, dst_txt_filename, trim_video_data, content, video_fps=25
):
    # -- save video
    save2vid(dst_vid_filename, trim_video_data, video_fps)
    # -- save text
    os.makedirs(os.path.dirname(dst_txt_filename), exist_ok=True)
    f = open(dst_txt_filename, "w")
    f.write(f"{content}")
    f.close()


def save_vid_aud(
    dst_vid_filename,
    dst_aud_filename,
    trim_vid_data,
    trim_aud_data,
    video_fps=25,
    audio_sample_rate=16000,
):
    # -- save video with embedded audio
    save2vid(dst_vid_filename, trim_vid_data, video_fps, audio_data=trim_aud_data, audio_sample_rate=audio_sample_rate)
    # -- also save audio separately for compatibility
    if dst_aud_filename is not None:
        save2aud(dst_aud_filename, trim_aud_data, audio_sample_rate)


def save_vid_aud_txt(
    dst_vid_filename,
    dst_aud_filename,
    dst_txt_filename,
    trim_vid_data,
    trim_aud_data,
    content,
    video_fps=25,
    audio_sample_rate=16000,
):
    # -- save video with embedded audio
    if dst_vid_filename is not None:
        save2vid(dst_vid_filename, trim_vid_data, video_fps, audio_data=trim_aud_data, audio_sample_rate=audio_sample_rate)
    # -- also save audio separately for compatibility
    if dst_aud_filename is not None:
        save2aud(dst_aud_filename, trim_aud_data, audio_sample_rate)
    # -- save text
    os.makedirs(os.path.dirname(dst_txt_filename), exist_ok=True)
    f = open(dst_txt_filename, "w")
    f.write(f"{content}")
    f.close()


def save2vid(filename, vid, frames_per_second, audio_data=None, audio_sample_rate=16000):
    """
    Save video with optional audio muxing.

    Args:
        filename: Output mp4 path
        vid: Video tensor (T, H, W, C)
        frames_per_second: Video FPS
        audio_data: Optional audio tensor (C, N) or None
        audio_sample_rate: Audio sample rate (default 16000)
    """
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    if audio_data is None:
        # No audio - use original method
        torchvision.io.write_video(filename, vid, frames_per_second)
    else:
        # Have audio - save both and mux with ffmpeg
        import subprocess

        # Save video-only to temp file
        video_only = filename.replace('.mp4', '_video_only_tmp.mp4')
        torchvision.io.write_video(video_only, vid, frames_per_second)

        # Save audio to temp file
        audio_only = filename.replace('.mp4', '_audio_only_tmp.wav')
        torchaudio.save(audio_only, audio_data, audio_sample_rate)

        # Mux video and audio with ffmpeg
        try:
            subprocess.run([
                'ffmpeg', '-y', '-loglevel', 'error',
                '-i', video_only,
                '-i', audio_only,
                '-c:v', 'copy',
                '-c:a', 'aac',
                '-strict', 'experimental',
                filename
            ], check=True, capture_output=True)

            # Clean up temp files
            os.remove(video_only)
            os.remove(audio_only)
        except subprocess.CalledProcessError as e:
            # If muxing fails, keep video-only file and print warning
            print(f"Warning: Failed to mux audio into {filename}: {e.stderr.decode()}")
            if os.path.exists(video_only):
                os.rename(video_only, filename)
            if os.path.exists(audio_only):
                os.remove(audio_only)


def save2aud(filename, aud, sample_rate):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    torchaudio.save(filename, aud, sample_rate)
