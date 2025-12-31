#!/usr/bin/env python3
"""Generate sample artifacts for the extended report example.

This script creates all necessary artifact files (metrics, tables, figures)
with realistic sample data for testing the pipeline.
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime

# Base directory
BASE_DIR = Path(__file__).parent
ARTIFACTS_DIR = BASE_DIR / "artifacts"

# Ensure directories exist
(ARTIFACTS_DIR / "metrics").mkdir(parents=True, exist_ok=True)
(ARTIFACTS_DIR / "tables").mkdir(parents=True, exist_ok=True)
(ARTIFACTS_DIR / "figures").mkdir(parents=True, exist_ok=True)


def write_json(path: Path, data: dict) -> str:
    """Write JSON file and return SHA256 hash."""
    content = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    path.write_text(content)
    return "sha256:" + hashlib.sha256(content.encode()).hexdigest()


def write_binary(path: Path, data: bytes) -> str:
    """Write binary file and return SHA256 hash."""
    path.write_bytes(data)
    return "sha256:" + hashlib.sha256(data).hexdigest()


# Create a simple 1x1 PNG (red pixel) for figures
MINIMAL_PNG = bytes([
    0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
    0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,  # IHDR chunk
    0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,  # 1x1
    0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,
    0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,  # IDAT chunk
    0x54, 0x08, 0xD7, 0x63, 0xF8, 0xCF, 0xC0, 0x00,
    0x00, 0x00, 0x03, 0x00, 0x01, 0x00, 0x18, 0xDD,
    0x8D, 0xB4, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45,  # IEND chunk
    0x4E, 0x44, 0xAE, 0x42, 0x60, 0x82
])


def main():
    hashes = {}

    # =========================================================================
    # METRICS
    # =========================================================================

    metrics = {
        "overall_accuracy": {"label": "Overall System Accuracy", "value": 96.7, "unit": "%"},
        "latency_p99": {"label": "P99 Latency", "value": 23.4, "unit": "ms"},
        "face_precision": {"label": "Face Detection Precision", "value": 98.2, "unit": "%"},
        "face_recall": {"label": "Face Detection Recall", "value": 97.8, "unit": "%"},
        "gaze_angular_error": {"label": "Gaze Angular Error", "value": 4.2, "unit": "degrees"},
        "eye_perclos": {"label": "PERCLOS Accuracy", "value": 94.5, "unit": "%"},
        "yawn_detection": {"label": "Yawn Detection F1", "value": 0.923, "unit": ""},
        "attention_score": {"label": "Attention Score Accuracy", "value": 91.3, "unit": "%"},
        "multioccupant_accuracy": {"label": "Multi-Occupant Detection", "value": 87.2, "unit": "%",
                                   "notes": ["Preliminary results", "Not validated for production"]},
        "safety_score": {"label": "Composite Safety Score", "value": 94.8, "unit": "%",
                        "notes": ["Computed per ISO 26262 guidelines"]},
    }

    for name, data in metrics.items():
        path = ARTIFACTS_DIR / "metrics" / f"{name}.json"
        hashes[f"metrics/{name}.json"] = write_json(path, data)
        print(f"Created: {path}")

    # =========================================================================
    # TABLES (simple format)
    # =========================================================================

    tables = {
        "executive_summary": {
            "columns": [
                {"key": "category", "label": "Category"},
                {"key": "metric", "label": "Metric"},
                {"key": "value", "label": "Value"},
                {"key": "target", "label": "Target"},
                {"key": "status", "label": "Status"},
            ],
            "rows": [
                {"category": "Detection", "metric": "Face Detection", "value": "98.0%", "target": ">95%", "status": "PASS"},
                {"category": "Detection", "metric": "Eye Detection", "value": "96.5%", "target": ">95%", "status": "PASS"},
                {"category": "Estimation", "metric": "Gaze Accuracy", "value": "4.2°", "target": "<5°", "status": "PASS"},
                {"category": "Estimation", "metric": "Pose Accuracy", "value": "3.1°", "target": "<5°", "status": "PASS"},
                {"category": "Classification", "metric": "Drowsiness", "value": "94.5%", "target": ">90%", "status": "PASS"},
                {"category": "Classification", "metric": "Distraction", "value": "91.3%", "target": ">90%", "status": "PASS"},
                {"category": "Performance", "metric": "Latency P99", "value": "23.4ms", "target": "<30ms", "status": "PASS"},
            ],
        },
        "face_detection_lighting": {
            "columns": [
                {"key": "condition", "label": "Lighting Condition"},
                {"key": "precision", "label": "Precision", "dtype": "float"},
                {"key": "recall", "label": "Recall", "dtype": "float"},
                {"key": "f1", "label": "F1 Score", "dtype": "float"},
                {"key": "samples", "label": "Samples", "dtype": "int"},
            ],
            "rows": [
                {"condition": "Daylight", "precision": 98.5, "recall": 98.2, "f1": 98.3, "samples": 45000},
                {"condition": "Night (IR)", "precision": 97.2, "recall": 96.8, "f1": 97.0, "samples": 38000},
                {"condition": "Dusk/Dawn", "precision": 96.8, "recall": 96.1, "f1": 96.4, "samples": 22000},
                {"condition": "Tunnel Exit", "precision": 94.5, "recall": 93.8, "f1": 94.1, "samples": 8000},
                {"condition": "Direct Sunlight", "precision": 95.2, "recall": 94.6, "f1": 94.9, "samples": 12000},
            ],
        },
        "pose_yaw": {
            "columns": [
                {"key": "range", "label": "Yaw Range"},
                {"key": "mae", "label": "MAE (degrees)", "dtype": "float"},
                {"key": "std", "label": "Std Dev", "dtype": "float"},
                {"key": "samples", "label": "Samples", "dtype": "int"},
            ],
            "rows": [
                {"range": "-90° to -60°", "mae": 5.8, "std": 2.1, "samples": 8500},
                {"range": "-60° to -30°", "mae": 3.2, "std": 1.4, "samples": 22000},
                {"range": "-30° to 0°", "mae": 2.1, "std": 0.9, "samples": 45000},
                {"range": "0° to 30°", "mae": 2.0, "std": 0.8, "samples": 48000},
                {"range": "30° to 60°", "mae": 3.4, "std": 1.5, "samples": 21000},
                {"range": "60° to 90°", "mae": 6.1, "std": 2.3, "samples": 7500},
            ],
        },
        "pose_pitch": {
            "columns": [
                {"key": "range", "label": "Pitch Range"},
                {"key": "mae", "label": "MAE (degrees)", "dtype": "float"},
                {"key": "std", "label": "Std Dev", "dtype": "float"},
            ],
            "rows": [
                {"range": "-45° to -30°", "mae": 4.2, "std": 1.8},
                {"range": "-30° to -15°", "mae": 2.8, "std": 1.2},
                {"range": "-15° to 15°", "mae": 1.9, "std": 0.7},
                {"range": "15° to 30°", "mae": 2.6, "std": 1.1},
                {"range": "30° to 45°", "mae": 4.5, "std": 1.9},
            ],
        },
        "gaze_by_region": {
            "columns": [
                {"key": "region", "label": "Gaze Region"},
                {"key": "accuracy", "label": "Accuracy (%)", "dtype": "float"},
                {"key": "samples", "label": "Samples", "dtype": "int"},
            ],
            "rows": [
                {"region": "Road Ahead", "accuracy": 96.2, "samples": 85000},
                {"region": "Instrument Cluster", "accuracy": 93.8, "samples": 25000},
                {"region": "Center Console", "accuracy": 94.5, "samples": 18000},
                {"region": "Left Mirror", "accuracy": 98.1, "samples": 8000},
                {"region": "Right Mirror", "accuracy": 97.8, "samples": 7500},
                {"region": "Rear View Mirror", "accuracy": 95.2, "samples": 6500},
            ],
        },
        "gaze_zone_confusion": {
            "columns": [
                {"key": "actual", "label": "Actual Zone"},
                {"key": "road", "label": "→ Road", "dtype": "float"},
                {"key": "instrument", "label": "→ Instrument", "dtype": "float"},
                {"key": "console", "label": "→ Console", "dtype": "float"},
                {"key": "mirror_l", "label": "→ L Mirror", "dtype": "float"},
                {"key": "mirror_r", "label": "→ R Mirror", "dtype": "float"},
                {"key": "phone", "label": "→ Phone", "dtype": "float"},
            ],
            "rows": [
                {"actual": "Road", "road": 96.2, "instrument": 2.1, "console": 0.8, "mirror_l": 0.3, "mirror_r": 0.3, "phone": 0.3},
                {"actual": "Instrument", "road": 3.8, "instrument": 93.8, "console": 1.5, "mirror_l": 0.2, "mirror_r": 0.2, "phone": 0.5},
                {"actual": "Console", "road": 1.2, "instrument": 2.3, "console": 94.5, "mirror_l": 0.1, "mirror_r": 0.1, "phone": 1.8},
                {"actual": "L Mirror", "road": 0.8, "instrument": 0.3, "console": 0.1, "mirror_l": 98.1, "mirror_r": 0.5, "phone": 0.2},
                {"actual": "R Mirror", "road": 0.9, "instrument": 0.4, "console": 0.1, "mirror_l": 0.6, "mirror_r": 97.8, "phone": 0.2},
                {"actual": "Phone", "road": 0.5, "instrument": 1.2, "console": 3.5, "mirror_l": 0.1, "mirror_r": 0.1, "phone": 94.6},
            ],
        },
        "eye_blink_metrics": {
            "columns": [
                {"key": "metric", "label": "Metric"},
                {"key": "value", "label": "Value"},
                {"key": "unit", "label": "Unit"},
                {"key": "threshold", "label": "Alert Threshold"},
            ],
            "rows": [
                {"metric": "Blink Detection Rate", "value": "97.2%", "unit": "", "threshold": ">95%"},
                {"metric": "Mean Blink Duration", "value": "215", "unit": "ms", "threshold": ">400ms"},
                {"metric": "PERCLOS (1 min)", "value": "8.3%", "unit": "", "threshold": ">15%"},
                {"metric": "Blink Rate", "value": "14.2", "unit": "blinks/min", "threshold": "<8 or >25"},
            ],
        },
        "yawn_temporal": {
            "columns": [
                {"key": "phase", "label": "Detection Phase"},
                {"key": "accuracy", "label": "Accuracy (%)", "dtype": "float"},
                {"key": "latency", "label": "Latency (ms)", "dtype": "int"},
            ],
            "rows": [
                {"phase": "Onset Detection", "accuracy": 94.2, "latency": 85},
                {"phase": "Peak Detection", "accuracy": 97.8, "latency": 120},
                {"phase": "End Detection", "accuracy": 91.5, "latency": 95},
                {"phase": "Duration Estimation", "accuracy": 88.3, "latency": 0},
            ],
        },
        "distraction_activities": {
            "columns": [
                {"key": "activity", "label": "Activity"},
                {"key": "precision", "label": "Precision", "dtype": "float"},
                {"key": "recall", "label": "Recall", "dtype": "float"},
                {"key": "f1", "label": "F1", "dtype": "float"},
            ],
            "rows": [
                {"activity": "Phone Usage", "precision": 95.2, "recall": 93.3, "f1": 94.2},
                {"activity": "Texting", "precision": 92.1, "recall": 89.5, "f1": 90.8},
                {"activity": "Eating/Drinking", "precision": 81.2, "recall": 75.6, "f1": 78.3},
                {"activity": "Reaching Back", "precision": 88.5, "recall": 85.2, "f1": 86.8},
                {"activity": "Talking to Passenger", "precision": 79.8, "recall": 82.1, "f1": 80.9},
                {"activity": "Adjusting Controls", "precision": 86.3, "recall": 84.7, "f1": 85.5},
            ],
        },
        "attention_thresholds": {
            "columns": [
                {"key": "level", "label": "Attention Level"},
                {"key": "score_range", "label": "Score Range"},
                {"key": "action", "label": "System Action"},
                {"key": "occurrence", "label": "Occurrence (%)", "dtype": "float"},
            ],
            "rows": [
                {"level": "Fully Attentive", "score_range": "90-100", "action": "None", "occurrence": 78.5},
                {"level": "Mild Distraction", "score_range": "70-89", "action": "Visual Alert", "occurrence": 15.2},
                {"level": "Moderate Distraction", "score_range": "50-69", "action": "Audio Alert", "occurrence": 4.8},
                {"level": "Severe Distraction", "score_range": "30-49", "action": "Haptic + Audio", "occurrence": 1.2},
                {"level": "Critical", "score_range": "0-29", "action": "Emergency Protocol", "occurrence": 0.3},
            ],
        },
        "latency_breakdown": {
            "columns": [
                {"key": "stage", "label": "Processing Stage"},
                {"key": "mean", "label": "Mean (ms)", "dtype": "float"},
                {"key": "p50", "label": "P50 (ms)", "dtype": "float"},
                {"key": "p99", "label": "P99 (ms)", "dtype": "float"},
            ],
            "rows": [
                {"stage": "Image Preprocessing", "mean": 1.2, "p50": 1.1, "p99": 2.1},
                {"stage": "Face Detection", "mean": 4.5, "p50": 4.2, "p99": 6.8},
                {"stage": "Landmark Extraction", "mean": 2.8, "p50": 2.6, "p99": 4.2},
                {"stage": "Pose Estimation", "mean": 3.2, "p50": 3.0, "p99": 5.1},
                {"stage": "Gaze Estimation", "mean": 2.1, "p50": 2.0, "p99": 3.5},
                {"stage": "Classification", "mean": 1.8, "p50": 1.7, "p99": 2.9},
                {"stage": "Post-processing", "mean": 0.8, "p50": 0.7, "p99": 1.2},
                {"stage": "Total", "mean": 16.4, "p50": 15.3, "p99": 23.4},
            ],
        },
        "resource_utilization": {
            "columns": [
                {"key": "resource", "label": "Resource"},
                {"key": "mean", "label": "Mean Usage"},
                {"key": "peak", "label": "Peak Usage"},
                {"key": "limit", "label": "Limit"},
            ],
            "rows": [
                {"resource": "CPU", "mean": "45%", "peak": "62%", "limit": "70%"},
                {"resource": "GPU", "mean": "38%", "peak": "55%", "limit": "80%"},
                {"resource": "Memory", "mean": "512 MB", "peak": "680 MB", "limit": "1 GB"},
                {"resource": "NPU", "mean": "72%", "peak": "85%", "limit": "100%"},
            ],
        },
        # Internal-only tables
        "failures_by_category": {
            "columns": [
                {"key": "category", "label": "Failure Category"},
                {"key": "count", "label": "Count", "dtype": "int"},
                {"key": "percentage", "label": "Percentage", "dtype": "float"},
                {"key": "severity", "label": "Severity"},
            ],
            "rows": [
                {"category": "Sunglasses (reflective)", "count": 1842, "percentage": 23.1, "severity": "High"},
                {"category": "Extreme Pose", "count": 1456, "percentage": 18.3, "severity": "Medium"},
                {"category": "Motion Blur", "count": 1123, "percentage": 14.1, "severity": "Medium"},
                {"category": "Occlusion (hand)", "count": 987, "percentage": 12.4, "severity": "Medium"},
                {"category": "Low Contrast", "count": 856, "percentage": 10.7, "severity": "Low"},
                {"category": "IR Saturation", "count": 723, "percentage": 9.1, "severity": "High"},
                {"category": "Multiple Faces", "count": 512, "percentage": 6.4, "severity": "Low"},
                {"category": "Other", "count": 471, "percentage": 5.9, "severity": "Low"},
            ],
        },
        "edge_cases_catalog": {
            "columns": [
                {"key": "id", "label": "Case ID"},
                {"key": "description", "label": "Description"},
                {"key": "frequency", "label": "Frequency"},
                {"key": "status", "label": "Status"},
            ],
            "rows": [
                {"id": "EC-001", "description": "Polarized sunglasses with IR reflection", "frequency": "Rare", "status": "Under Investigation"},
                {"id": "EC-002", "description": "Face tattoos affecting landmark detection", "frequency": "Very Rare", "status": "Known Issue"},
                {"id": "EC-003", "description": "Extreme backlight during sunset", "frequency": "Occasional", "status": "Mitigated"},
                {"id": "EC-004", "description": "Medical eye patches", "frequency": "Very Rare", "status": "Documented"},
                {"id": "EC-005", "description": "Face masks (post-COVID)", "frequency": "Common", "status": "Resolved"},
            ],
        },
        "debug_feature_stats": {
            "columns": [
                {"key": "feature", "label": "Feature"},
                {"key": "mean", "label": "Mean", "dtype": "float"},
                {"key": "std", "label": "Std", "dtype": "float"},
                {"key": "min", "label": "Min", "dtype": "float"},
                {"key": "max", "label": "Max", "dtype": "float"},
            ],
            "rows": [
                {"feature": "face_confidence", "mean": 0.92, "std": 0.08, "min": 0.51, "max": 0.99},
                {"feature": "eye_aspect_ratio", "mean": 0.28, "std": 0.05, "min": 0.12, "max": 0.45},
                {"feature": "mouth_aspect_ratio", "mean": 0.15, "std": 0.12, "min": 0.02, "max": 0.68},
                {"feature": "head_pose_yaw", "mean": -2.3, "std": 18.5, "min": -85.2, "max": 82.1},
                {"feature": "gaze_pitch", "mean": -8.5, "std": 12.3, "min": -45.0, "max": 35.2},
            ],
        },
        # Draft tables
        "multioccupant_positions": {
            "columns": [
                {"key": "position", "label": "Seating Position"},
                {"key": "detection_rate", "label": "Detection Rate", "dtype": "float"},
                {"key": "notes", "label": "Notes"},
            ],
            "rows": [
                {"position": "Driver", "detection_rate": 99.2, "notes": "Primary target"},
                {"position": "Front Passenger", "detection_rate": 94.5, "notes": "Good coverage"},
                {"position": "Rear Left", "detection_rate": 78.3, "notes": "Limited FOV"},
                {"position": "Rear Center", "detection_rate": 65.2, "notes": "Occluded"},
                {"position": "Rear Right", "detection_rate": 76.8, "notes": "Limited FOV"},
            ],
        },
        "emotion_preliminary": {
            "columns": [
                {"key": "emotion", "label": "Emotion"},
                {"key": "accuracy", "label": "Accuracy", "dtype": "float"},
                {"key": "status", "label": "Status"},
            ],
            "rows": [
                {"emotion": "Neutral", "accuracy": 82.5, "status": "WIP"},
                {"emotion": "Happy", "accuracy": 75.2, "status": "WIP"},
                {"emotion": "Angry", "accuracy": 68.3, "status": "WIP"},
                {"emotion": "Surprised", "accuracy": 71.8, "status": "WIP"},
                {"emotion": "Drowsy", "accuracy": 88.2, "status": "Validated"},
            ],
        },
        # Verbose tables (large, for presentation filter testing)
        "verbose_per_subject": {
            "columns": [
                {"key": "subject_id", "label": "Subject ID"},
                {"key": "age_group", "label": "Age Group"},
                {"key": "gender", "label": "Gender"},
                {"key": "accuracy", "label": "Accuracy", "dtype": "float"},
                {"key": "sessions", "label": "Sessions", "dtype": "int"},
            ],
            "rows": [{"subject_id": f"S{i:04d}", "age_group": ["18-25", "26-35", "36-45", "46-55", "56+"][i % 5],
                     "gender": ["M", "F"][i % 2], "accuracy": 90.0 + (i % 10), "sessions": 3 + (i % 5)}
                    for i in range(100)],
        },
        "verbose_per_frame": {
            "columns": [
                {"key": "frame_id", "label": "Frame"},
                {"key": "confidence", "label": "Confidence", "dtype": "float"},
                {"key": "yaw", "label": "Yaw", "dtype": "float"},
                {"key": "pitch", "label": "Pitch", "dtype": "float"},
                {"key": "gaze_x", "label": "Gaze X", "dtype": "float"},
                {"key": "gaze_y", "label": "Gaze Y", "dtype": "float"},
            ],
            "rows": [{"frame_id": f"F{i:06d}", "confidence": 0.85 + (i % 15) * 0.01,
                     "yaw": -30 + (i % 60), "pitch": -15 + (i % 30),
                     "gaze_x": -20 + (i % 40), "gaze_y": -10 + (i % 20)}
                    for i in range(200)],
        },
        "verbose_feature_distributions": {
            "columns": [
                {"key": "bin", "label": "Bin"},
                {"key": "face_conf", "label": "Face Conf", "dtype": "int"},
                {"key": "eye_ar", "label": "Eye AR", "dtype": "int"},
                {"key": "mouth_ar", "label": "Mouth AR", "dtype": "int"},
            ],
            "rows": [{"bin": f"{i*10}-{(i+1)*10}", "face_conf": 50 + i * 20,
                     "eye_ar": 30 + i * 15, "mouth_ar": 20 + i * 10}
                    for i in range(10)],
        },
        # Dossier tables
        "regulatory_summary": {
            "columns": [
                {"key": "requirement", "label": "Regulatory Requirement"},
                {"key": "standard", "label": "Standard"},
                {"key": "result", "label": "Test Result"},
                {"key": "compliance", "label": "Compliance"},
            ],
            "rows": [
                {"requirement": "Driver Attention Detection", "standard": "UNECE R79", "result": "PASS", "compliance": "Compliant"},
                {"requirement": "Drowsiness Warning", "standard": "EU 2019/2144", "result": "PASS", "compliance": "Compliant"},
                {"requirement": "Distraction Warning", "standard": "EU 2019/2144", "result": "PASS", "compliance": "Compliant"},
                {"requirement": "System Availability", "standard": "ISO 26262", "result": "99.2%", "compliance": "ASIL-B"},
                {"requirement": "False Positive Rate", "standard": "Internal", "result": "<2%", "compliance": "Compliant"},
            ],
        },
    }

    for name, data in tables.items():
        path = ARTIFACTS_DIR / "tables" / f"{name}.json"
        hashes[f"tables/{name}.json"] = write_json(path, data)
        print(f"Created: {path}")

    # =========================================================================
    # FIGURES (placeholder PNGs)
    # =========================================================================

    figures = [
        "pose_error_dist",
        "gaze_heatmap",
        "drowsiness_roc",
        "distraction_confusion",
        "latency_histogram",
        "edge_cases_examples",
    ]

    for name in figures:
        path = ARTIFACTS_DIR / "figures" / f"{name}.png"
        hashes[f"figures/{name}.png"] = write_binary(path, MINIMAL_PNG)

        # Create meta file
        meta_path = ARTIFACTS_DIR / "figures" / f"{name}.meta.json"
        meta_data = {
            "caption": f"Visualization: {name.replace('_', ' ').title()}",
            "alt": f"Figure showing {name.replace('_', ' ')}",
        }
        hashes[f"figures/{name}.meta.json"] = write_json(meta_path, meta_data)
        print(f"Created: {path} + meta")

    # =========================================================================
    # Print hash summary for AARC registry
    # =========================================================================

    print("\n" + "=" * 60)
    print("SHA256 Hashes for AARC Registry:")
    print("=" * 60)
    for uri, sha in sorted(hashes.items()):
        print(f'"{uri}": "{sha}"')


if __name__ == "__main__":
    main()
