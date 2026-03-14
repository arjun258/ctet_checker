# ============================================================
# CTET OMRChecker - Per-Sheet CSV Solution
# ============================================================
#
# THE PROBLEM:
#   In src/utils/file.py, OMRChecker uses:
#       TIME_NOW_HRS = strftime("%I%p", localtime())
#       "Results": f"Results_{TIME_NOW_HRS}.csv"
#   This groups ALL sheets checked in the same hour into one CSV.
#
# THE FIX:
#   Two-part solution:
#   1. Patch src/utils/file.py to use a timestamp down to the second
#      (so each run gets a unique CSV)
#   2. Use a wrapper script (run_omr.py) that:
#      - Accepts a candidate name / roll number as argument
#      - Runs OMRChecker with a unique --outputDir per candidate
#      - Renames the resulting CSV to <candidate_id>_results.csv
#      - Prints the CSV path for your backend to consume
#
# ============================================================


# ============================================================
# PART 1: PATCH TO APPLY IN src/utils/file.py
# ============================================================
#
# FIND this block (around line 20-30 of src/utils/file.py):
#
#     TIME_NOW_HRS = strftime("%I%p", localtime())
#     ns.filesMap = {
#         "Results": os.path.join(paths.results_dir, f"Results_{TIME_NOW_HRS}.csv"),
#         "MultiMarked": os.path.join(paths.manual_dir, "MultiMarkedFiles.csv"),
#         "Errors": os.path.join(paths.manual_dir, "ErrorFiles.csv"),
#     }
#
# REPLACE WITH:
#
#     import os as _os
#     _custom_prefix = _os.environ.get("OMR_SESSION_ID", None)
#     if _custom_prefix:
#         _result_name = f"Results_{_custom_prefix}.csv"
#     else:
#         TIME_NOW_HRS = strftime("%Y%m%d_%H%M%S", localtime())   # second-level unique
#         _result_name = f"Results_{TIME_NOW_HRS}.csv"
#     ns.filesMap = {
#         "Results": os.path.join(paths.results_dir, _result_name),
#         "MultiMarked": os.path.join(paths.manual_dir, "MultiMarkedFiles.csv"),
#         "Errors": os.path.join(paths.manual_dir, "ErrorFiles.csv"),
#     }
#
# This means:
#   - If you set the env variable OMR_SESSION_ID, the CSV will be
#     named  Results_<OMR_SESSION_ID>.csv  (e.g. Results_RAHUL_001.csv)
#   - If you don't set it, it falls back to a second-level timestamp
#     (Results_20260313_142305.csv) — unique per run, never collides
# ============================================================


# ============================================================
# PART 2: WRAPPER SCRIPT  (save as run_omr.py in OMRChecker root)
# ============================================================
# Usage:
#   python run_omr.py --candidate "Rahul_Sharma" --image "path/to/omr.jpg"
#
# What it does:
#   1. Copies the image into a fresh temp input folder
#   2. Sets OMR_SESSION_ID env var to the candidate name
#   3. Runs OMRChecker → output goes to outputs/<candidate_id>/
#   4. Finds the Results CSV and returns the path
# ============================================================

import argparse
import os
import shutil
import subprocess
import sys
import glob
from datetime import datetime

def run_omr_for_candidate(candidate_id: str, image_path: str, omrchecker_dir: str = "."):
    """
    Run OMRChecker for a single candidate and get a uniquely named CSV.

    Args:
        candidate_id : Unique ID for this candidate, e.g. "Rahul_Sharma_001"
                       (used as CSV name, avoid spaces — use underscores)
        image_path   : Full path to the candidate's OMR image file
        omrchecker_dir: Path to the OMRChecker root folder (default: current dir)

    Returns:
        str: Path to the resulting CSV file
    """
    # Sanitize candidate_id (no spaces, no special chars)
    safe_id = candidate_id.strip().replace(" ", "_").replace("/", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_id = f"{safe_id}_{timestamp}"

    # Create a clean temp input folder for this candidate
    input_dir = os.path.join(omrchecker_dir, "inputs", f"session_{session_id}")
    images_dir = os.path.join(input_dir, "IMAGES")
    os.makedirs(images_dir, exist_ok=True)

    # Copy candidate's OMR image into the temp folder
    img_filename = os.path.basename(image_path)
    dest_image = os.path.join(images_dir, img_filename)
    shutil.copy2(image_path, dest_image)

    # Copy template.json from parent inputs folder (required by OMRChecker)
    template_src = os.path.join(omrchecker_dir, "inputs", "template.json")
    if os.path.exists(template_src):
        shutil.copy2(template_src, os.path.join(input_dir, "template.json"))
    else:
        # Try to find it in any existing input subfolder
        for tmpl in glob.glob(os.path.join(omrchecker_dir, "inputs", "**", "template.json"), recursive=True):
            shutil.copy2(tmpl, os.path.join(input_dir, "template.json"))
            break

    # Output folder unique to this candidate
    output_dir = os.path.join(omrchecker_dir, "outputs", f"session_{session_id}")
    os.makedirs(output_dir, exist_ok=True)

    # Set environment variable so patched file.py uses our session_id as CSV name
    env = os.environ.copy()
    env["OMR_SESSION_ID"] = session_id

    # Run OMRChecker
    cmd = [
        sys.executable, "main.py",
        "--inputDir", input_dir,
        "--outputDir", output_dir
    ]

    print(f"\n[OMR] Running for candidate: {candidate_id}")
    print(f"[OMR] Session ID: {session_id}")
    print(f"[OMR] Command: {' '.join(cmd)}")

    result = subprocess.run(
        cmd,
        cwd=omrchecker_dir,
        env=env,
        capture_output=False   # show OMRChecker output in terminal
    )

    if result.returncode != 0:
        raise RuntimeError(f"OMRChecker failed with exit code {result.returncode}")

    # Find the CSV that was created
    csv_pattern = os.path.join(output_dir, "**", f"Results_{session_id}.csv")
    matches = glob.glob(csv_pattern, recursive=True)

    if not matches:
        # Fallback: find any Results CSV in output dir
        matches = glob.glob(os.path.join(output_dir, "**", "Results_*.csv"), recursive=True)

    if not matches:
        raise FileNotFoundError(
            f"Could not find Results CSV in {output_dir}\n"
            f"Make sure you applied the patch to src/utils/file.py"
        )

    csv_path = matches[0]
    print(f"\n[OMR] ✅ CSV saved: {csv_path}")
    return csv_path


def parse_csv(csv_path: str) -> dict:
    """
    Parse OMRChecker output CSV and return {q_num: letter} dict.
    Skips blank/header rows automatically.
    """
    import csv
    answers = {}
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Skip completely empty rows
            if not row.get('file_id') and not any(row.values()):
                continue
            # Skip the blank spacer row OMRChecker sometimes adds
            if not row.get('q001'):
                continue
            for key, val in row.items():
                key = key.strip().lower()
                if key.startswith('q') and key[1:].isdigit():
                    q_num = int(key[1:])
                    answers[q_num] = val.strip().upper()
            break  # Only first data row per file
    return answers


# ============================================================
# CLI entry point
# ============================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run OMRChecker for a single candidate and get uniquely named output CSV"
    )
    parser.add_argument(
        "--candidate",
        required=True,
        help='Candidate ID, e.g. "Rahul_Sharma" or "ROLL_2024_001"'
    )
    parser.add_argument(
        "--image",
        required=True,
        help="Path to candidate OMR image file (jpg/png)"
    )
    parser.add_argument(
        "--omrdir",
        default=".",
        help="Path to OMRChecker root directory (default: current directory)"
    )
    parser.add_argument(
        "--check-score",
        action="store_true",
        help="Also run CTET answer checking after OMR extraction"
    )

    args = parser.parse_args()

    # Run OMR extraction
    csv_path = run_omr_for_candidate(
        candidate_id=args.candidate,
        image_path=args.image,
        omrchecker_dir=args.omrdir
    )

    # Optionally run CTET score check
    if args.check_score:
        print("\n[CTET] Parsed answers from CSV:")
        answers = parse_csv(csv_path)
        for q in range(1, 151):
            print(f"  Q{q:03d}: {answers.get(q, '—')}", end="\t")
            if q % 10 == 0:
                print()

    print(f"\n[DONE] CSV: {csv_path}")