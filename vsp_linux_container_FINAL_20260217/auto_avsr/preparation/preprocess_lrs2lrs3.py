import argparse
import glob
import math
import os
import warnings
import shutil
import ffmpeg
import pickle

from data.data_module import AVSRDataLoader
from tqdm import tqdm
from transforms import TextTransform
from utils import save_vid_aud_txt, split_file

warnings.filterwarnings("ignore")


def _make_silent_audio_like(trim_vid_data, sample_rate=16000, fps=25):
    """
    Create silent audio with the correct length for downstream code.
    16000/25 = 640 samples per frame.
    Returns shape [1, T*640].
    """
    num_frames = int(len(trim_vid_data))
    num_samples = num_frames * (sample_rate // fps)
    try:
        import torch
        return torch.zeros(1, num_samples, dtype=torch.float32)
    except Exception:
        import numpy as np
        return np.zeros((1, num_samples), dtype=np.float32)


def to_gray(frames):
    """
    Convert (T,H,W,C) -> (T,H,W) grayscale if C==3/1.
    Leaves (T,H,W) untouched.
    Supports torch or numpy.
    """
    # torch?
    try:
        import torch
        if torch.is_tensor(frames):
            x = frames
            if x.ndim == 3:
                return x
            if x.ndim == 4 and x.shape[-1] in (1, 3):
                if x.shape[-1] == 1:
                    return x[..., 0]
                r = x[..., 0].float()
                g = x[..., 1].float()
                b = x[..., 2].float()
                y = 0.2989 * r + 0.5870 * g + 0.1140 * b
                return y.to(dtype=x.dtype)
            return x
    except Exception:
        pass

    import numpy as np
    arr = frames
    if arr.ndim == 3:
        return arr
    if arr.ndim == 4 and arr.shape[-1] in (1, 3):
        if arr.shape[-1] == 1:
            return arr[..., 0]
        r = arr[..., 0].astype(np.float32)
        g = arr[..., 1].astype(np.float32)
        b = arr[..., 2].astype(np.float32)
        y = 0.2989 * r + 0.5870 * g + 0.1140 * b
        return y.astype(arr.dtype)
    return arr

def gray_to_rgb3(frames):
    """
    Ensure video frames are (T,H,W,3) even if grayscale.
    If input is (T,H,W) -> replicate to 3 channels.
    If input is (T,H,W,1) -> replicate to 3 channels.
    Leaves (T,H,W,3) untouched.
    Works for torch or numpy.
    """
    # torch?
    try:
        import torch
        if torch.is_tensor(frames):
            if frames.ndim == 3:  # (T,H,W)
                return frames.unsqueeze(-1).repeat(1, 1, 1, 3)
            if frames.ndim == 4 and frames.shape[-1] == 1:
                return frames.repeat(1, 1, 1, 3)
            return frames
    except Exception:
        pass

    import numpy as np
    arr = frames
    if arr.ndim == 3:  # (T,H,W)
        return np.repeat(arr[..., None], 3, axis=-1)
    if arr.ndim == 4 and arr.shape[-1] == 1:
        return np.repeat(arr, 3, axis=-1)
    return arr


def pad_or_center_crop_to_square(frames, out_size=96, pad_value=0):
    """
    Make frames exactly (T,out_size,out_size) by:
      - center crop if bigger
      - symmetric pad if smaller
    NO resize.
    Supports (T,H,W) or (T,H,W,C), torch or numpy.
    """
    is_torch = False
    torch = None
    try:
        import torch as _torch
        torch = _torch
        is_torch = torch.is_tensor(frames)
    except Exception:
        pass

    if is_torch:
        arr = frames.detach().cpu().numpy()
        device = frames.device
        dtype = frames.dtype
    else:
        arr = frames
        device = None
        dtype = None

    if arr.ndim not in (3, 4):
        raise ValueError(f"Unexpected frames shape {arr.shape}")

    H, W = arr.shape[1], arr.shape[2]

    # center crop
    if H > out_size:
        top = (H - out_size) // 2
        arr = arr[:, top : top + out_size, ...]
        H = out_size
    if W > out_size:
        left = (W - out_size) // 2
        arr = arr[:, :, left : left + out_size, ...]
        W = out_size

    # pad
    pad_h = max(0, out_size - H)
    pad_w = max(0, out_size - W)
    top = pad_h // 2
    bottom = pad_h - top
    left = pad_w // 2
    right = pad_w - left

    if pad_h > 0 or pad_w > 0:
        import numpy as np
        if arr.ndim == 4:
            arr = np.pad(
                arr,
                ((0, 0), (top, bottom), (left, right), (0, 0)),
                mode="constant",
                constant_values=pad_value,
            )
        else:
            arr = np.pad(
                arr,
                ((0, 0), (top, bottom), (left, right)),
                mode="constant",
                constant_values=pad_value,
            )

    if is_torch:
        out = torch.from_numpy(arr).to(device=device)
        try:
            out = out.to(dtype=dtype)
        except Exception:
            pass
        return out

    return arr


# ------------------ args ------------------
parser = argparse.ArgumentParser(description="LRS2/LRS3/flat Preprocessing (keep mediapipe + your flat robustness)")
parser.add_argument("--data-dir", type=str, required=True)
parser.add_argument("--detector", type=str, default="mediapipe")  # DO NOT CHANGE
parser.add_argument("--landmarks-dir", type=str, default=None)
parser.add_argument("--root-dir", type=str, required=True)
parser.add_argument("--subset", type=str, required=True)
parser.add_argument("--dataset", type=str, required=True)
parser.add_argument("--gpu_type", type=str, default="cuda")
parser.add_argument("--seg-duration", type=int, default=16)
parser.add_argument("--disable-segmentation", action="store_true", help="Process videos as whole files without segmentation")
parser.add_argument("--combine-av", type=lambda x: str(x).lower() == "true", default=False)
parser.add_argument("--groups", type=int, default=1)
parser.add_argument("--job-index", type=int, default=0)

# paper-like output knobs
parser.add_argument("--mouth_size", type=int, default=96)
parser.add_argument("--force_gray", type=lambda x: str(x).lower() == "true", default=True)

args = parser.parse_args()

seg_duration = args.seg_duration
dataset = args.dataset
text_transform = TextTransform()

args.data_dir = os.path.normpath(args.data_dir)
if args.gpu_type not in ["cuda", "mps"]:
    raise ValueError('gpu_type must be "cuda" or "mps"')

vid_dataloader = AVSRDataLoader(
    modality="video",
    detector=args.detector,   # stays mediapipe unless user overrides
    convert_gray=False,       # we gray ourselves (safer)
    gpu_type=args.gpu_type,
)
aud_dataloader = AVSRDataLoader(modality="audio")

seg_vid_len = seg_duration * 25  # frames

# Determine directory naming: use "whole" for non-segmented, "seg{duration}s" for segmented
dir_suffix = "whole" if args.disable_segmentation else f"seg{seg_duration}s"

label_filename = os.path.join(
    args.root_dir,
    "labels",
    f"{dataset}_{args.subset}_transcript_lengths_{dir_suffix}.csv"
    if args.groups <= 1
    else f"{dataset}_{args.subset}_transcript_lengths_{dir_suffix}.{args.groups}.{args.job_index}.csv",
)
os.makedirs(os.path.dirname(label_filename), exist_ok=True)

dst_vid_dir = os.path.join(args.root_dir, dataset, f"{dataset}_video_{dir_suffix}")
dst_txt_dir = os.path.join(args.root_dir, dataset, f"{dataset}_text_{dir_suffix}")
os.makedirs(dst_vid_dir, exist_ok=True)
os.makedirs(dst_txt_dir, exist_ok=True)


def apply_paper_like_video(x):
    if args.force_gray:
        x = to_gray(x)  # may become (T,H,W)
    x = pad_or_center_crop_to_square(x, out_size=args.mouth_size, pad_value=0)
    # torchvision.write_video wants (T,H,W,C). keep grayscale by replicating to 3ch.
    x = gray_to_rgb3(x)
    return x


# -------- file discovery (original + your flat) --------
if dataset == "flat":
    filenames = sorted(glob.glob(os.path.join(args.data_dir, "*.mp4")))
elif dataset == "lrs3":
    if args.subset == "test":
        filenames = glob.glob(os.path.join(args.data_dir, args.subset, "**", "*.mp4"), recursive=True)
    elif args.subset == "train":
        filenames = glob.glob(os.path.join(args.data_dir, "trainval", "**", "*.mp4"), recursive=True)
        filenames.extend(glob.glob(os.path.join(args.data_dir, "pretrain", "**", "*.mp4"), recursive=True))
        filenames.sort()
    else:
        raise NotImplementedError(f"lrs3 subset {args.subset} not supported")
elif dataset == "lrs2":
    if args.subset in ["val", "test", "train"]:
        list_path = os.path.join(os.path.dirname(args.data_dir), f"{args.subset}.txt")
        filenames = [
            os.path.join(args.data_dir, "main", ln.split()[0] + ".mp4")
            for ln in open(list_path).read().splitlines()
        ]
        if args.subset == "train":
            pretrain_list = os.path.join(os.path.dirname(args.data_dir), "pretrain.txt")
            pretrain_filenames = [
                os.path.join(args.data_dir, "pretrain", ln.split()[0] + ".mp4")
                for ln in open(pretrain_list).read().splitlines()
            ]
            filenames.extend(pretrain_filenames)
            filenames.sort()
    else:
        raise NotImplementedError(f"lrs2 subset {args.subset} not supported")
else:
    raise NotImplementedError(f"Only flat/lrs2/lrs3 supported, got {dataset}")

# shard
unit = math.ceil(len(filenames) / args.groups) if args.groups > 0 else len(filenames)
filenames = filenames[args.job_index * unit : (args.job_index + 1) * unit]


with open(label_filename, "w", encoding="utf-8") as f:
    for data_filename in tqdm(filenames):
        # landmarks (optional, like original)
        if args.landmarks_dir:
            landmarks_filename = data_filename.replace(args.data_dir, args.landmarks_dir)[:-4] + ".pkl"
            try:
                landmarks = pickle.load(open(landmarks_filename, "rb"))
            except Exception:
                landmarks = None
        else:
            landmarks = None

        # load video
        try:
            video_data = vid_dataloader.load_data(data_filename, landmarks)
        except Exception:
            continue
        if video_data is None or len(video_data) == 0:
            continue

        # load audio with your robust fallback
        try:
            audio_data = aud_dataloader.load_data(data_filename)
        except Exception:
            audio_data = None
        if audio_data is None:
            audio_data = _make_silent_audio_like(video_data, sample_rate=16000, fps=25)
        else:
            try:
                if audio_data.size(1) == 0:
                    audio_data = _make_silent_audio_like(video_data, sample_rate=16000, fps=25)
            except Exception:
                audio_data = _make_silent_audio_like(video_data, sample_rate=16000, fps=25)

        # ---------------- FLAT (your pipeline behavior) ----------------
        if dataset == "flat":
            trim_vid_data, trim_aud_data = video_data, audio_data

            # transcript fallback: if missing -> "no audio"
            txt_path = data_filename[:-4] + ".txt"
            if os.path.exists(txt_path):
                try:
                    with open(txt_path, "r", encoding="utf-8") as ft:
                        content = ft.read().strip()
                except Exception:
                    content = ""
            else:
                content = ""
            if not content:
                content = "no audio"

            trim_vid_data = apply_paper_like_video(trim_vid_data)

            dst_vid_filename = f"{data_filename.replace(args.data_dir, dst_vid_dir)[:-4]}.mp4"
            dst_aud_filename = f"{data_filename.replace(args.data_dir, dst_vid_dir)[:-4]}.wav"
            dst_txt_filename = f"{data_filename.replace(args.data_dir, dst_txt_dir)[:-4]}.txt"
            os.makedirs(os.path.dirname(dst_vid_filename), exist_ok=True)
            os.makedirs(os.path.dirname(dst_txt_filename), exist_ok=True)

            save_vid_aud_txt(
                dst_vid_filename,
                dst_aud_filename,
                dst_txt_filename,
                trim_vid_data,
                trim_aud_data,
                content,
                video_fps=25,
                audio_sample_rate=16000,
            )

            if args.combine_av:
                in1 = ffmpeg.input(dst_vid_filename)
                in2 = ffmpeg.input(dst_aud_filename)
                out = ffmpeg.output(
                    in1["v"], in2["a"],
                    dst_vid_filename[:-4] + ".av.mp4",
                    vcodec="copy", acodec="aac",
                    strict="experimental", loglevel="panic",
                )
                out.run()
                shutil.move(dst_vid_filename[:-4] + ".av.mp4", dst_vid_filename)

            basename = os.path.relpath(dst_vid_filename, start=os.path.join(args.root_dir, dataset))
            token_id_str = " ".join(map(str, [_.item() for _ in text_transform.tokenize(content)]))
            if token_id_str:
                try:
                    nframes = int(trim_vid_data.shape[0])
                except Exception:
                    nframes = int(len(trim_vid_data))
                f.write(f"{dataset},{basename},{nframes},{token_id_str}\n")
            continue

        # ---------------- ORIGINAL "main/trainval/test direct txt parse" path ----------------
        parts = os.path.normpath(data_filename).split(os.sep)
        third_from_end = parts[-3] if len(parts) >= 3 else ""
        if third_from_end in ["trainval", "test", "main"]:
            dst_vid_filename = f"{data_filename.replace(args.data_dir, dst_vid_dir)[:-4]}.mp4"
            dst_aud_filename = f"{data_filename.replace(args.data_dir, dst_vid_dir)[:-4]}.wav"
            dst_txt_filename = f"{data_filename.replace(args.data_dir, dst_txt_dir)[:-4]}.txt"
            trim_vid_data, trim_aud_data = video_data, audio_data

            try:
                text_line_list = open(data_filename[:-4] + ".txt", "r").read().splitlines()[0].split(" ")
                text_line = " ".join(text_line_list[2:])
                content = text_line.replace("}", "").replace("{", "")
            except Exception:
                content = ""
            if not content:
                content = "no audio"

            trim_vid_data = apply_paper_like_video(trim_vid_data)

            save_vid_aud_txt(
                dst_vid_filename,
                dst_aud_filename,
                dst_txt_filename,
                trim_vid_data,
                trim_aud_data,
                content,
                video_fps=25,
                audio_sample_rate=16000,
            )

            if args.combine_av:
                in1 = ffmpeg.input(dst_vid_filename)
                in2 = ffmpeg.input(dst_aud_filename)
                out = ffmpeg.output(
                    in1["v"], in2["a"],
                    dst_vid_filename[:-4] + ".av.mp4",
                    vcodec="copy", acodec="aac",
                    strict="experimental", loglevel="panic",
                )
                out.run()
                shutil.move(dst_vid_filename[:-4] + ".av.mp4", dst_vid_filename)

            basename = os.path.relpath(dst_vid_filename, start=os.path.join(args.root_dir, dataset))
            token_id_str = " ".join(map(str, [_.item() for _ in text_transform.tokenize(content)]))
            f.write(f"{dataset},{basename},{trim_vid_data.shape[0]},{token_id_str}\n")
            continue

        # ---------------- ORIGINAL segmentation path (split_file) ----------------
        # Skip segmentation if --disable-segmentation flag is set
        if args.disable_segmentation:
            # Process as single whole video
            splitted = [(content if content else "no audio", 0.0, len(video_data) / 25.0, len(video_data) / 25.0)]
        else:
            # Normal segmentation path
            try:
                splitted = split_file(data_filename[:-4] + ".txt", max_frames=seg_vid_len)
            except Exception:
                continue

        for i in range(len(splitted)):
            content, start, end, duration = splitted[i]
            if not content:
                content = "no audio"

            if len(splitted) == 1:
                trim_vid_data, trim_aud_data = video_data, audio_data
            else:
                start_idx, end_idx = int(start * 25), int(end * 25)
                try:
                    trim_vid_data = video_data[start_idx:end_idx]
                    trim_aud_data = audio_data[:, start_idx * 640 : end_idx * 640]
                except Exception:
                    continue

            if trim_vid_data is None or trim_aud_data is None:
                continue
            try:
                if len(trim_vid_data) == 0 or trim_aud_data.size(1) == 0:
                    continue
            except Exception:
                continue

            trim_vid_data = apply_paper_like_video(trim_vid_data)

            dst_vid_filename = f"{data_filename.replace(args.data_dir, dst_vid_dir)[:-4]}_{i:02d}.mp4"
            dst_aud_filename = f"{data_filename.replace(args.data_dir, dst_vid_dir)[:-4]}_{i:02d}.wav"
            dst_txt_filename = f"{data_filename.replace(args.data_dir, dst_txt_dir)[:-4]}_{i:02d}.txt"

            save_vid_aud_txt(
                dst_vid_filename,
                dst_aud_filename,
                dst_txt_filename,
                trim_vid_data,
                trim_aud_data,
                content,
                video_fps=25,
                audio_sample_rate=16000,
            )

            if args.combine_av:
                in1 = ffmpeg.input(dst_vid_filename)
                in2 = ffmpeg.input(dst_aud_filename)
                out = ffmpeg.output(
                    in1["v"], in2["a"],
                    dst_vid_filename[:-4] + ".av.mp4",
                    vcodec="copy", acodec="aac",
                    strict="experimental", loglevel="panic",
                )
                out.run()
                try:
                    os.remove(dst_aud_filename)
                except Exception:
                    pass
                shutil.move(dst_vid_filename[:-4] + ".av.mp4", dst_vid_filename)

            basename = os.path.relpath(dst_vid_filename, start=os.path.join(args.root_dir, dataset))
            token_id_str = " ".join(map(str, [_.item() for _ in text_transform.tokenize(content)]))
            if token_id_str:
                f.write(f"{dataset},{basename},{trim_vid_data.shape[0]},{token_id_str}\n")