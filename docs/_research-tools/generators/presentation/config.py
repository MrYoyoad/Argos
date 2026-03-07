"""
Presentation configuration — paths, colors, layout constants.
"""

import os
from pathlib import Path
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor

# ═══════════════════════════════════════════════════════════════════════
# PATHS
# ═══════════════════════════════════════════════════════════════════════

SCRIPT_DIR = Path(__file__).parent.parent   # generators/
MATERIALS = Path("/home/ubuntu/presentation_materials_20260224")
PLOTS = MATERIALS / "01_plots_for_slides"
BRANDING = MATERIALS / "08_branding"
VIDEOS = MATERIALS / "06_demo_videos"
OUTPUT = MATERIALS / "Argos_VSP_Project_Review.pptx"

# Image map
IMG = {
    "logo": BRANDING / "BlackLogo300x300-W-BG.png",
    "pipeline": PLOTS / "pipeline_architecture.png",
    "model_arch": PLOTS / "model_architecture.png",
    "P1_quality": PLOTS / "P1_quality_tiers.png",
    "P2_paper": PLOTS / "P2_paper_vs_reality.png",
    "P3_trajectory": PLOTS / "P3_wer_trajectory.png",
    "P3b_is_trajectory": PLOTS / "P3b_is_trajectory.png",
    "P4_lenpen": PLOTS / "P4_lenpen_sensitivity.png",
    "boxplot": PLOTS / "09_boxplot_wwer_all_experiments.png",
    "wer_duration": PLOTS / "01_wer_vs_duration.png",
    "nea_scatter": PLOTS / "14_nea_vs_wwer_scatter.png",
    "empty_halluc": PLOTS / "10_empty_and_hallucination_rates.png",
    "cdf_wwer": PLOTS / "15_cdf_wwer_curated.png",
    "ft_dashboard": PLOTS / "finetune" / "FT_10_summary_dashboard.png",
    "ft_clean": PLOTS / "finetune" / "FT_11_clean_summary.png",
    "ft_loss": PLOTS / "finetune" / "FT_11a_loss.png",
    "ft_impact": PLOTS / "finetune" / "FT_11b_impact.png",
    "tuning_ba": PLOTS / "P5_tuning_before_after.png",
    "improve_ja": PLOTS / "16_improvement_J_vs_A.png",
    "P6_is_radar": PLOTS / "P6_is_radar.png",
    "P6b_radar_dual": PLOTS / "P6b_radar_dual.png",
    "P7_is_wer_scatter": PLOTS / "P7_is_wer_scatter.png",
    "pipeline_visual": PLOTS / "pipeline_visual_strip.png",
}

VID = {
    # Curated examples (Slide 14)
    "perfect":        VIDEOS / "IEa7qEkMvfQ_3__c5447488_with_hyp.mp4",
    "bogo":           VIDEOS / "d8BR6hsvzoY_31__2e9546df_with_hyp.mp4",
    "nearmiss":       VIDEOS / "-WQZsfHcPDM_7__5210cac1_with_hyp.mp4",
    "halluc":         VIDEOS / "00MUdHQ7GGY_8__b1480c7a_with_hyp.mp4",
    "tuning_fix":     VIDEOS / "DBhaa45mAro_2__07d05c7a_Part1_with_hyp.mp4",
    "topic_drift":    VIDEOS / "vBCnI4kf3-E_0__d2216cbf_Part1_with_hyp.mp4",
    "salvage":        VIDEOS / "Q8aPjew1aUU_5__621126f2_with_hyp.mp4",
    # Failure modes / salvage (A11b, A13)
    "extreme_halluc": VIDEOS / "BmmJujNQvXw_0__5d6e5798_with_hyp.mp4",
    "phonetic_bridge":VIDEOS / "cT6aHJmM4cA_2__a0c6120f_with_hyp.mp4",
    "wer_broken":     VIDEOS / "0FUlRjBcGGE_21__8fc418e2_with_hyp.mp4",
    "entity_success": VIDEOS / "BS4kTgaiydQ_0__10c532bb_with_hyp.mp4",
    "entity_destroy": VIDEOS / "EMfcKvHA5Uc_0__b74dba61_with_hyp.mp4",
    "admiral":        VIDEOS / "-POZpyVCN8k_9__c7b26ea8_with_hyp.mp4",
    "vitamin_d":      VIDEOS / "2dwUMlphEnI_5__c6ce8f09_with_hyp.mp4",
    "ok_demo":        VIDEOS / "8SMYkCQkT4Q_0__fdf516a0_with_hyp.mp4",
    # New batch (36 videos burned 2026-03-07)
    "hypertension":   VIDEOS / "0v2N6w4m46s_0__964e9355_with_hyp.mp4",
    "convention":     VIDEOS / "MoaWM3RwJAM_7__f04f26c6_with_hyp.mp4",
    "marilyn":        VIDEOS / "-n1y0QwPq1I_1__d2eebee8_with_hyp.mp4",
    "music_play":     VIDEOS / "elY8NW20jQ0_1__e07d6605_with_hyp.mp4",
    "spelling_smell": VIDEOS / "eUIoJsvKJ4E_0__f480a719_with_hyp.mp4",
    "doxology":       VIDEOS / "tOWDLscXYGI_0__ec79306b_with_hyp.mp4",
    "street_photo":   VIDEOS / "2HddWQse8Mw_0__8ecb0409_with_hyp.mp4",
}

POSTER_DIR = MATERIALS / ".poster_frames"

# ═══════════════════════════════════════════════════════════════════════
# DESIGN CONSTANTS
# ═══════════════════════════════════════════════════════════════════════

# Slide size (16:9 widescreen)
SL_W = Emu(12192000)   # 13.333 in
SL_H = Emu(6858000)    # 7.5 in

# Colors
BG      = RGBColor(0x0D, 0x1B, 0x2A)  # deep navy
WHITE   = RGBColor(0xFF, 0xFF, 0xFF)
TEAL    = RGBColor(0x00, 0xB4, 0xD8)
CORAL   = RGBColor(0xE0, 0x6C, 0x75)
LGRAY   = RGBColor(0xAA, 0xAA, 0xAA)
MGRAY   = RGBColor(0x66, 0x66, 0x66)
DGRAY   = RGBColor(0x33, 0x33, 0x33)
GREEN   = RGBColor(0x4C, 0xAF, 0x50)
YELLOW  = RGBColor(0xFF, 0xC1, 0x07)
GOLD    = RGBColor(0xFF, 0xD5, 0x4F)
ORANGE  = RGBColor(0xFF, 0x98, 0x00)
RED     = RGBColor(0xF4, 0x43, 0x36)
DRED    = RGBColor(0xB7, 0x1C, 0x1C)
NAVY2   = RGBColor(0x15, 0x2A, 0x40)  # slightly lighter navy for cards
NAVY3   = RGBColor(0x1A, 0x35, 0x50)  # lighter still for hover cards

FONT = "Calibri"

# Auto-numbering: incremented by _finish() for each main slide
_auto_num = [0]

# Layout (inches)
MX   = Inches(0.6)      # horizontal margin
MY   = Inches(0.4)      # top margin
CT   = Inches(1.45)     # content top (below title + accent)
CW   = Inches(12.13)    # content width (SL_W - 2*MX)
CH   = Inches(5.55)     # content height
SLW  = Inches(5.6)      # split left width
SRG  = Inches(0.3)      # split gap
SRL  = Inches(6.5)      # split right left
SRW  = Inches(5.93)     # split right width
