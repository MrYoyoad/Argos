#!/usr/bin/env python3
"""
Generate conflict report from merged predictions.

Highlights disagreements between overlapping segments for user review.

Usage:
    python generate_conflict_report.py \
        --merged-json decode/vsr/en/hypo-123-merged.json \
        --output-dir client_outputs/conflicts
"""

import argparse
import json
from pathlib import Path
from typing import List, Dict


def write_json_report(conflicts: List[Dict], output_path: Path):
    """Write conflicts to JSON file."""
    with open(output_path, 'w') as f:
        json.dump(conflicts, f, indent=2)
    print(f"  ✓ JSON report: {output_path}")


def write_text_report(conflicts: List[Dict], output_path: Path):
    """Write conflicts to plain text file."""
    with open(output_path, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("OVERLAP CONFLICT REPORT\n")
        f.write("=" * 80 + "\n\n")
        
        if not conflicts:
            f.write("No conflicts detected. All overlapping segments had consistent predictions.\n")
            return
        
        f.write(f"Total conflicts: {len(conflicts)}\n\n")
        
        for i, conflict in enumerate(conflicts, 1):
            f.write(f"Conflict #{i}\n")
            f.write("-" * 80 + "\n")
            f.write(f"Time: {conflict['overlap_time'][0]:.1f}s - {conflict['overlap_time'][1]:.1f}s\n")
            f.write(f"Similarity: {conflict['similarity']:.1%}\n\n")
            f.write(f"CHOSEN ({conflict['chosen_source']}):\n")
            f.write(f"  \"{conflict['chosen_text']}\"\n\n")
            f.write(f"ALTERNATE ({conflict['alternate_source']}):\n")
            f.write(f"  \"{conflict['alternate_text']}\"\n\n")
    
    print(f"  ✓ Text report: {output_path}")


def write_html_report(conflicts: List[Dict], output_path: Path):
    """Write conflicts to HTML file."""
    html = """
<!DOCTYPE html>
<html>
<head>
    <title>Overlap Conflict Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        h1 { color: #333; }
        .conflict { border: 1px solid #ddd; margin: 20px 0; padding: 15px; border-radius: 5px; }
        .time { color: #666; font-size: 14px; }
        .similarity { color: #999; font-size: 12px; }
        .chosen { background: #e8f5e9; padding: 10px; margin: 10px 0; border-left: 4px solid #4caf50; }
        .alternate { background: #fff3e0; padding: 10px; margin: 10px 0; border-left: 4px solid #ff9800; }
        .label { font-weight: bold; font-size: 12px; text-transform: uppercase; }
    </style>
</head>
<body>
    <h1>Overlap Conflict Report</h1>
"""
    
    if not conflicts:
        html += "<p>No conflicts detected. All overlapping segments had consistent predictions.</p>"
    else:
        html += f"<p>Total conflicts: {len(conflicts)}</p>"
        
        for i, conflict in enumerate(conflicts, 1):
            html += f"""
    <div class="conflict">
        <h3>Conflict #{i}</h3>
        <div class="time">Time: {conflict['overlap_time'][0]:.1f}s - {conflict['overlap_time'][1]:.1f}s</div>
        <div class="similarity">Similarity: {conflict['similarity']:.1%}</div>
        
        <div class="chosen">
            <div class="label">Chosen ({conflict['chosen_source']})</div>
            <p>"{conflict['chosen_text']}"</p>
        </div>
        
        <div class="alternate">
            <div class="label">Alternate ({conflict['alternate_source']})</div>
            <p>"{conflict['alternate_text']}"</p>
        </div>
    </div>
"""
    
    html += """
</body>
</html>
"""
    
    with open(output_path, 'w') as f:
        f.write(html)
    
    print(f"  ✓ HTML report: {output_path}")


def generate_conflict_report(merged_json_path: Path, output_dir: Path):
    """Generate conflict reports from merged predictions."""
    
    # Load merged output
    try:
        with open(merged_json_path, 'r') as f:
            merged_data = json.load(f)
        print(f"✓ Loaded merged predictions from {merged_json_path}")
    except FileNotFoundError:
        print(f"ERROR: Merged JSON not found: {merged_json_path}")
        return
    
    # Extract all conflicts
    all_conflicts = []
    for video_id, video_data in merged_data.items():
        if 'conflicts' in video_data and video_data['conflicts']:
            for conflict in video_data['conflicts']:
                # Add video context
                conflict['video_id'] = video_id
                all_conflicts.append(conflict)
    
    print(f"  Found {len(all_conflicts)} conflicts across {len(merged_data)} videos")
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate reports in multiple formats
    write_json_report(all_conflicts, output_dir / "conflicts.json")
    write_text_report(all_conflicts, output_dir / "conflicts.txt")
    write_html_report(all_conflicts, output_dir / "conflicts.html")
    
    print(f"\n✓ Conflict reports generated in {output_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate conflict report")
    parser.add_argument("--merged-json", required=True, help="Path to merged JSON")
    parser.add_argument("--output-dir", required=True, help="Output directory for reports")
    
    args = parser.parse_args()
    generate_conflict_report(Path(args.merged_json), Path(args.output_dir))
