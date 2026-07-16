import cv2, glob, os, statistics
import mediapipe as mp
mesh = mp.solutions.face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1, refine_landmarks=False, min_detection_confidence=0.4)
def mouth_px(path, n=4):
    cap = cv2.VideoCapture(path); tot = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)); ws = []
    H = W = None
    for i in range(n):
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(tot*(i+0.5)/n)); ok, fr = cap.read()
        if not ok: continue
        H, W = fr.shape[:2]
        r = mesh.process(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB))
        if not r.multi_face_landmarks: continue
        lm = r.multi_face_landmarks[0].landmark
        mw = abs(lm[291].x-lm[61].x)*W; fw = abs(lm[454].x-lm[234].x)*W
        ws.append((mw, fw))
    cap.release()
    if not ws: return None, None, (W,H)
    return statistics.median(w[0] for w in ws), statistics.median(w[1] for w in ws), (W,H)

groups = {
 "iPhone-4K decode inputs (img_*)": "/home/ubuntu/datasets/clients/egla_kafe/work/decode/in_shaam_all/img_68*.mp4",
 "screen-rec decode inputs (shaam_*)": "/home/ubuntu/datasets/clients/egla_kafe/work/decode/in_shaam_all/shaam_*.mp4",
 "screen-rec decode inputs (s1/s2)": "/home/ubuntu/datasets/clients/egla_kafe/work/decode/in_scene12_all/s*_*.mp4",
 "ABLATION res4k_ctrl crops": "/home/ubuntu/datasets/clients/egla_kafe_resolution/res4k_ctrl/work/crops_src/*.mp4",
 "ABLATION res2k crops": "/home/ubuntu/datasets/clients/egla_kafe_resolution/res2k/work/crops_src/*.mp4",
 "ABLATION res1080 crops": "/home/ubuntu/datasets/clients/egla_kafe_resolution/res1080/work/crops_src/*.mp4",
}
for label, pat in groups.items():
    files = sorted(glob.glob(pat))
    if not files: print(f"\n== {label} ==\n  no files"); continue
    bystem = {}
    for f in files:
        b = os.path.basename(f)
        parts = b.replace(".mp4","").split("_")
        stem = "_".join(parts[:2]) if b.startswith("img") else "_".join(parts[:4]) if b.startswith("shaam") else "_".join(parts[:4])
        bystem.setdefault(stem, []).append(f)
    print(f"\n== {label} ==")
    for stem, fl in sorted(bystem.items()):
        vals = [mouth_px(f) for f in fl[:2]]
        vals = [(m,fw,dim) for m,fw,dim in vals if m]
        if not vals: print(f"  {stem}: no face found in samples"); continue
        m = statistics.median(v[0] for v in vals); fw = statistics.median(v[1] for v in vals); dim = vals[0][2]
        flag = "OK (>=96)" if m >= 96 else "BELOW 96-px crop"
        print(f"  {stem}: frame {dim[0]}x{dim[1]}, face~{fw:.0f}px, MOUTH~{m:.0f}px  [{flag}]")
