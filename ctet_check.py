"""
ctet_check.py  —  Place this in your OMRChecker root folder.

USAGE:
    py ctet_check.py

It will ask you step by step:
  1. Path to the OMR image
  2. Subject (Math/Science or Social Studies) and Set
  3. Language 1 and Set
  4. Language 2 and Set

Then it runs OMRChecker, reads the CSV, checks answers, and prints the score.
"""

import csv
import glob
import os
import shutil
import subprocess
import sys
import uuid
from datetime import datetime


# ════════════════════════════════════════════════════════════════
# ANSWER KEY DATABASE
# ════════════════════════════════════════════════════════════════

ANSWER_KEYS = {
    "math_science": {
        "Set_G": {1:'2',2:'2',3:'3',4:'2',5:'1',6:'4',7:'1',8:'3',9:'3',10:'1',11:'1',12:'1',13:'3',14:'4',15:'3',16:'3',17:'2',18:'1',19:'2',20:'2',21:'3',22:'3',23:'4',24:'3',25:'1',26:'3',27:'3',28:'3',29:'1',30:'2',31:'3',32:'1',33:'2',34:'3',35:'2',36:'3',37:'2',38:'1',39:'4',40:'3',41:'1',42:'3',43:'3',44:'1',45:'4',46:'2',47:'4',48:'2',49:'1',50:'1',51:'4',52:'1',53:'2',54:'2',55:'4',56:'2',57:'Z',58:'1',59:'3',60:'4',61:'4',62:'3',63:'3',64:'1',65:'1',66:'3',67:'1',68:'4',69:'3',70:'1',71:'3',72:'4',73:'2',74:'2',75:'1',76:'2',77:'4',78:'Z',79:'3',80:'1',81:'1',82:'4',83:'1',84:'Z',85:'2',86:'1',87:'3',88:'1',89:'2',90:'3'},
        "Set_H": {1:'3',2:'1',3:'3',4:'2',5:'4',6:'4',7:'4',8:'2',9:'1',10:'2',11:'4',12:'4',13:'2',14:'4',15:'4',16:'4',17:'2',18:'4',19:'1',20:'2',21:'2',22:'4',23:'3',24:'3',25:'4',26:'2',27:'3',28:'4',29:'3',30:'3',31:'2',32:'3',33:'2',34:'3',35:'1',36:'3',37:'2',38:'4',39:'4',40:'2',41:'3',42:'2',43:'3',44:'3',45:'1',46:'2',47:'3',48:'3',49:'2',50:'4',51:'4',52:'4',53:'4',54:'4',55:'Z',56:'1',57:'1',58:'1',59:'2',60:'1',61:'4',62:'2',63:'4',64:'Z',65:'2',66:'Z',67:'2',68:'3',69:'4',70:'4',71:'3',72:'1',73:'2',74:'4',75:'4',76:'1',77:'2',78:'2',79:'3',80:'1',81:'2',82:'3',83:'2',84:'1',85:'4',86:'3',87:'4',88:'2',89:'2',90:'1'},
        "Set_I": {1:'1',2:'1',3:'4',4:'3',5:'4',6:'4',7:'1',8:'1',9:'4',10:'4',11:'4',12:'2',13:'2',14:'3',15:'1',16:'2',17:'2',18:'2',19:'2',20:'2',21:'2',22:'2',23:'2',24:'2',25:'3',26:'4',27:'4',28:'2',29:'1',30:'1',31:'3',32:'4',33:'4',34:'2',35:'2',36:'1',37:'3',38:'2',39:'2',40:'2',41:'3',42:'3',43:'3',44:'1',45:'4',46:'1',47:'2',48:'4',49:'Z',50:'4',51:'3',52:'4',53:'1',54:'1',55:'4',56:'1',57:'1',58:'1',59:'4',60:'2',61:'2',62:'4',63:'2',64:'2',65:'4',66:'4',67:'3',68:'3',69:'3',70:'1',71:'1',72:'4',73:'4',74:'4',75:'2',76:'Z',77:'1',78:'3',79:'2',80:'3',81:'2',82:'4',83:'4',84:'1',85:'1',86:'Z',87:'4',88:'2',89:'2',90:'4'},
        "Set_J": {1:'1',2:'4',3:'4',4:'1',5:'1',6:'1',7:'3',8:'4',9:'4',10:'1',11:'3',12:'3',13:'1',14:'1',15:'3',16:'1',17:'2',18:'3',19:'1',20:'3',21:'1',22:'2',23:'4',24:'3',25:'1',26:'1',27:'4',28:'2',29:'3',30:'4',31:'4',32:'3',33:'1',34:'4',35:'4',36:'4',37:'3',38:'2',39:'1',40:'3',41:'4',42:'1',43:'2',44:'3',45:'1',46:'1',47:'3',48:'2',49:'2',50:'1',51:'3',52:'1',53:'2',54:'4',55:'2',56:'Z',57:'3',58:'4',59:'4',60:'3',61:'Z',62:'1',63:'3',64:'3',65:'4',66:'1',67:'1',68:'2',69:'2',70:'2',71:'3',72:'3',73:'1',74:'2',75:'2',76:'4',77:'4',78:'4',79:'3',80:'4',81:'3',82:'1',83:'1',84:'3',85:'3',86:'1',87:'1',88:'3',89:'Z',90:'3'},
    },
    "social_science": {
        "Set_G": {1:'2',2:'2',3:'3',4:'2',5:'1',6:'4',7:'1',8:'3',9:'3',10:'1',11:'1',12:'1',13:'3',14:'4',15:'3',16:'3',17:'2',18:'1',19:'2',20:'2',21:'3',22:'3',23:'4',24:'3',25:'1',26:'3',27:'3',28:'3',29:'1',30:'2',31:'4',32:'1',33:'2',34:'3',35:'2',36:'1',37:'1',38:'3',39:'1',40:'2',41:'2',42:'1',43:'3',44:'2',45:'3',46:'1',47:'1',48:'1',49:'3',50:'2',51:'3',52:'4',53:'4',54:'1',55:'2',56:'4',57:'2',58:'4',59:'4',60:'2',61:'2',62:'2',63:'3',64:'3',65:'3',66:'2',67:'1',68:'1',69:'3',70:'3',71:'2',72:'4',73:'3',74:'3',75:'2',76:'2',77:'1',78:'2',79:'1',80:'2',81:'3',82:'4',83:'4',84:'4',85:'1',86:'4',87:'3',88:'3',89:'1',90:'2'},
        "Set_H": {1:'3',2:'1',3:'3',4:'2',5:'4',6:'4',7:'4',8:'2',9:'1',10:'2',11:'4',12:'4',13:'2',14:'4',15:'4',16:'4',17:'2',18:'4',19:'1',20:'2',21:'2',22:'4',23:'3',24:'3',25:'4',26:'2',27:'3',28:'4',29:'3',30:'3',31:'2',32:'1',33:'4',34:'2',35:'4',36:'2',37:'1',38:'1',39:'2',40:'3',41:'2',42:'1',43:'2',44:'3',45:'2',46:'4',47:'3',48:'1',49:'3',50:'2',51:'3',52:'4',53:'4',54:'1',55:'3',56:'3',57:'3',58:'4',59:'3',60:'2',61:'3',62:'1',63:'2',64:'3',65:'3',66:'1',67:'4',68:'2',69:'3',70:'3',71:'3',72:'1',73:'2',74:'4',75:'4',76:'2',77:'4',78:'1',79:'4',80:'1',81:'4',82:'4',83:'4',84:'3',85:'4',86:'3',87:'3',88:'4',89:'3',90:'2'},
        "Set_I": {1:'1',2:'1',3:'4',4:'3',5:'4',6:'4',7:'1',8:'1',9:'4',10:'4',11:'4',12:'2',13:'2',14:'3',15:'1',16:'2',17:'2',18:'2',19:'2',20:'2',21:'2',22:'2',23:'2',24:'2',25:'3',26:'4',27:'4',28:'2',29:'1',30:'1',31:'1',32:'1',33:'1',34:'4',35:'1',36:'4',37:'4',38:'3',39:'4',40:'3',41:'1',42:'2',43:'2',44:'3',45:'2',46:'4',47:'2',48:'3',49:'1',50:'2',51:'4',52:'3',53:'3',54:'4',55:'1',56:'4',57:'1',58:'1',59:'4',60:'2',61:'1',62:'1',63:'1',64:'1',65:'2',66:'4',67:'4',68:'1',69:'3',70:'4',71:'1',72:'1',73:'2',74:'3',75:'4',76:'3',77:'2',78:'3',79:'2',80:'4',81:'2',82:'2',83:'3',84:'1',85:'2',86:'1',87:'2',88:'2',89:'1',90:'2'},
        "Set_J": {1:'1',2:'4',3:'4',4:'1',5:'1',6:'1',7:'3',8:'4',9:'4',10:'1',11:'3',12:'3',13:'1',14:'1',15:'3',16:'1',17:'2',18:'3',19:'1',20:'3',21:'1',22:'2',23:'4',24:'3',25:'1',26:'1',27:'4',28:'2',29:'3',30:'4',31:'3',32:'1',33:'1',34:'2',35:'3',36:'4',37:'4',38:'3',39:'2',40:'2',41:'4',42:'4',43:'3',44:'1',45:'3',46:'1',47:'4',48:'4',49:'1',50:'2',51:'2',52:'3',53:'4',54:'3',55:'1',56:'4',57:'3',58:'2',59:'3',60:'4',61:'2',62:'3',63:'1',64:'2',65:'4',66:'1',67:'4',68:'3',69:'4',70:'2',71:'1',72:'1',73:'1',74:'3',75:'2',76:'1',77:'1',78:'4',79:'4',80:'3',81:'1',82:'4',83:'4',84:'3',85:'1',86:'1',87:'4',88:'2',89:'4',90:'4'},
    },
    "languages": {
        "English": {
            "Set_G": {91:'2',92:'4',93:'1',94:'1',95:'1',96:'2',97:'2',98:'4',99:'3',100:'2',101:'4',102:'1',103:'1',104:'1',105:'1',106:'1',107:'2',108:'2',109:'4',110:'1',111:'3',112:'1',113:'2',114:'4',115:'1',116:'1',117:'1',118:'4',119:'3',120:'1',121:'2',122:'3',123:'1',124:'1',125:'1',126:'2',127:'3',128:'1',129:'3',130:'3',131:'3',132:'4',133:'4',134:'1',135:'1',136:'2',137:'3',138:'2',139:'4',140:'2',141:'1',142:'4',143:'3',144:'2',145:'4',146:'2',147:'3',148:'4',149:'1',150:'2'},
            "Set_H": {91:'2',92:'3',93:'3',94:'3',95:'2',96:'1',97:'4',98:'2',99:'1',100:'2',101:'2',102:'2',103:'3',104:'2',105:'1',106:'3',107:'3',108:'2',109:'4',110:'1',111:'3',112:'2',113:'2',114:'2',115:'2',116:'1',117:'4',118:'2',119:'2',120:'1',121:'2',122:'3',123:'2',124:'2',125:'3',126:'4',127:'2',128:'4',129:'4',130:'2',131:'1',132:'4',133:'2',134:'4',135:'1',136:'3',137:'4',138:'3',139:'2',140:'1',141:'4',142:'3',143:'3',144:'4',145:'3',146:'3',147:'2',148:'1',149:'1',150:'1'},
            "Set_I": {91:'1',92:'3',93:'1',94:'4',95:'3',96:'4',97:'1',98:'2',99:'4',100:'3',101:'4',102:'4',103:'4',104:'1',105:'1',106:'4',107:'2',108:'1',109:'4',110:'2',111:'1',112:'1',113:'3',114:'4',115:'3',116:'4',117:'4',118:'4',119:'3',120:'4',121:'1',122:'4',123:'1',124:'4',125:'4',126:'4',127:'1',128:'1',129:'2',130:'3',131:'3',132:'4',133:'4',134:'2',135:'2',136:'3',137:'4',138:'2',139:'1',140:'4',141:'2',142:'1',143:'1',144:'1',145:'3',146:'2',147:'3',148:'2',149:'3',150:'4'},
            "Set_J": {91:'2',92:'1',93:'2',94:'3',95:'4',96:'3',97:'3',98:'4',99:'4',100:'3',101:'3',102:'4',103:'3',104:'2',105:'3',106:'1',107:'3',108:'3',109:'3',110:'3',111:'3',112:'1',113:'2',114:'2',115:'4',116:'4',117:'2',118:'4',119:'3',120:'3',121:'1',122:'4',123:'3',124:'3',125:'3',126:'4',127:'3',128:'1',129:'2',130:'1',131:'3',132:'1',133:'1',134:'2',135:'3',136:'3',137:'4',138:'1',139:'2',140:'4',141:'4',142:'3',143:'2',144:'2',145:'1',146:'1',147:'4',148:'4',149:'4',150:'2'},
        },
        "Hindi": {
            "Set_G": {91:'2',92:'1',93:'4',94:'4',95:'3',96:'1',97:'3',98:'3',99:'2',100:'1',101:'3',102:'2',103:'2',104:'3',105:'4',106:'1',107:'2',108:'2',109:'4',110:'1',111:'3',112:'1',113:'2',114:'4',115:'1',116:'1',117:'1',118:'4',119:'3',120:'1',121:'2',122:'2',123:'3',124:'4',125:'1',126:'1',127:'3',128:'4',129:'4',130:'4',131:'2',132:'3',133:'3',134:'1',135:'1',136:'2',137:'3',138:'2',139:'4',140:'2',141:'1',142:'4',143:'3',144:'2',145:'4',146:'2',147:'3',148:'4',149:'1',150:'2'},
            "Set_H": {91:'4',92:'3',93:'2',94:'2',95:'3',96:'3',97:'2',98:'2',99:'1',100:'1',101:'1',102:'4',103:'1',104:'1',105:'1',106:'3',107:'3',108:'2',109:'4',110:'1',111:'1',112:'2',113:'1',114:'1',115:'1',116:'1',117:'4',118:'3',119:'2',120:'1',121:'1',122:'3',123:'1',124:'1',125:'1',126:'4',127:'4',128:'4',129:'3',130:'2',131:'4',132:'1',133:'2',134:'1',135:'4',136:'3',137:'4',138:'2',139:'2',140:'1',141:'4',142:'3',143:'4',144:'4',145:'1',146:'2',147:'3',148:'1',149:'4',150:'2'},
            "Set_I": {91:'2',92:'2',93:'4',94:'2',95:'4',96:'3',97:'1',98:'1',99:'3',100:'2',101:'1',102:'3',103:'2',104:'1',105:'4',106:'4',107:'2',108:'1',109:'4',110:'2',111:'1',112:'1',113:'3',114:'4',115:'3',116:'4',117:'4',118:'4',119:'3',120:'4',121:'1',122:'3',123:'2',124:'4',125:'3',126:'2',127:'1',128:'4',129:'3',130:'2',131:'2',132:'4',133:'4',134:'1',135:'3',136:'3',137:'4',138:'2',139:'1',140:'4',141:'2',142:'1',143:'1',144:'1',145:'3',146:'3',147:'1',148:'1',149:'3',150:'2'},
            "Set_J": {91:'1',92:'4',93:'3',94:'2',95:'3',96:'1',97:'2',98:'4',99:'1',100:'4',101:'4',102:'3',103:'2',104:'1',105:'1',106:'3',107:'3',108:'3',109:'3',110:'3',111:'3',112:'1',113:'2',114:'2',115:'4',116:'4',117:'2',118:'4',119:'3',120:'3',121:'1',122:'3',123:'2',124:'1',125:'2',126:'1',127:'3',128:'4',129:'1',130:'4',131:'1',132:'1',133:'2',134:'1',135:'1',136:'1',137:'4',138:'1',139:'1',140:'1',141:'4',142:'3',143:'2',144:'3',145:'1',146:'1',147:'4',148:'4',149:'4',150:'2'},
        },
    },
}

LETTER_TO_NUM = {'A': '1', 'B': '2', 'C': '3', 'D': '4'}
NUM_TO_LETTER = {'1': 'A', '2': 'B', '3': 'C', '4': 'D', 'Z': 'Z'}


# ════════════════════════════════════════════════════════════════
# STEP 1 — COLLECT USER INPUT
# ════════════════════════════════════════════════════════════════

def ask(prompt, valid_options):
    """Ask a question and keep asking until the user gives a valid answer."""
    valid_lower = [v.lower() for v in valid_options]
    while True:
        answer = input(prompt).strip()
        if answer.lower() in valid_lower:
            # Return with original casing from valid_options
            return valid_options[valid_lower.index(answer.lower())]
        print(f"  Invalid input. Please enter one of: {', '.join(valid_options)}")


def collect_inputs():
    """Interactively ask the user for image path and paper details."""
    print("\n" + "="*55)
    print("        CTET PAPER-II ANSWER CHECKER")
    print("="*55)

    # ── Image path ────────────────────────────────────────────
    print("\nStep 1: OMR Image")
    print("  Enter the path to the OMR image file.")
    print("  Example: inputs\\CTET_TEST\\IMAGES\\IMAGE.jpeg")
    print()
    while True:
        image_path = input("  Image path: ").strip().strip('"').strip("'")
        # Normalize slashes
        image_path = image_path.replace("/", os.sep).replace("\\", os.sep).lstrip(os.sep)
        # Try relative to cwd, then absolute
        if os.path.isfile(image_path):
            image_path = os.path.abspath(image_path)
            break
        abs_try = os.path.abspath(image_path)
        if os.path.isfile(abs_try):
            image_path = abs_try
            break
        print(f"  File not found: {image_path}")
        print("  Please check the path and try again.")

    print(f"  ✓ Found: {image_path}")

    # ── Subject ───────────────────────────────────────────────
    print("\nStep 2: Subject (Q1–90)")
    subject_choice = ask(
        "  Subject — enter 'M' for Maths & Science, 'S' for Social Science: ",
        ["M", "S"]
    )
    subject_key = "math_science" if subject_choice == "M" else "social_science"
    subject_label = "Maths & Science" if subject_choice == "M" else "Social Science"

    subject_set = ask(
        "  Subject Set (G / H / I / J): ",
        ["G", "H", "I", "J"]
    )

    # ── Language 1 ────────────────────────────────────────────
    print("\nStep 3: Language 1 (Q91–120)")
    lang1 = ask(
        "  Language 1 — enter 'E' for English, 'H' for Hindi: ",
        ["E", "H"]
    )
    lang1_label = "English" if lang1 == "E" else "Hindi"
    lang1_set = ask(
        f"  Language 1 Set (G / H / I / J): ",
        ["G", "H", "I", "J"]
    )

    # ── Language 2 ────────────────────────────────────────────
    print("\nStep 4: Language 2 (Q121–150)")
    lang2 = ask(
        "  Language 2 — enter 'E' for English, 'H' for Hindi: ",
        ["E", "H"]
    )
    lang2_label = "English" if lang2 == "E" else "Hindi"
    lang2_set = ask(
        f"  Language 2 Set (G / H / I / J): ",
        ["G", "H", "I", "J"]
    )

    return {
        "image_path":    image_path,
        "subject_key":   subject_key,
        "subject_label": subject_label,
        "subject_set":   f"Set_{subject_set}",
        "lang1_label":   lang1_label,
        "lang1_set":     f"Set_{lang1_set}",
        "lang2_label":   lang2_label,
        "lang2_set":     f"Set_{lang2_set}",
    }


# ════════════════════════════════════════════════════════════════
# STEP 2 — RUN OMRCHECKER
# ════════════════════════════════════════════════════════════════

def find_template(omrchecker_dir):
    candidates = [
        os.path.join(omrchecker_dir, "templates", "template.json"),
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    
    return ""


def run_omrchecker(image_path, omrchecker_dir="."):
    """
    Copy image to a fresh isolated folder, run OMRChecker, return path to CSV.
    CSV is named with a random UUID — no candidate name dependency.
    """
    omrchecker_dir = os.path.abspath(omrchecker_dir)

    # Random session ID — no candidate names
    session_id = uuid.uuid4().hex[:12]   # e.g. "a3f9c1d82e4b"
    timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
    full_id    = f"{timestamp}_{session_id}"

    input_dir  = os.path.join(omrchecker_dir, "inputs",  f"session_{full_id}")
    images_dir = os.path.join(input_dir, "IMAGES")
    output_dir = os.path.join(omrchecker_dir, "outputs", f"session_{full_id}")

    os.makedirs(images_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    # Copy OMR image
    dest_image = os.path.join(images_dir, os.path.basename(image_path))
    shutil.copy2(image_path, dest_image)

    # Copy template
    template_src = find_template(omrchecker_dir)
    if template_src:
        shutil.copy2(template_src, os.path.join(input_dir, "template.json"))
    else:
        print("\n[WARN] template.json not found. OMRChecker may fail.")

    # Set session env var (used by patched src/utils/file.py)
    env = os.environ.copy()
    env["OMR_SESSION_ID"] = full_id

    cmd = [
        sys.executable,
        os.path.join(omrchecker_dir, "main.py"),
        "--inputDir",  input_dir,
        "--outputDir", output_dir,
    ]

    print(f"\n{'─'*55}")
    print(f"  Running OMRChecker...")
    print(f"  Session: {full_id}")
    print(f"{'─'*55}\n")

    result = subprocess.run(cmd, cwd=omrchecker_dir, env=env)

    if result.returncode != 0:
        print(f"\n[ERROR] OMRChecker failed (exit code {result.returncode})")
        sys.exit(result.returncode)

    # Find output CSV
    matches = glob.glob(os.path.join(output_dir, "**", f"Results_{full_id}.csv"), recursive=True)
    if not matches:
        matches = glob.glob(os.path.join(output_dir, "**", "Results_*.csv"), recursive=True)
    if not matches:
        print(f"\n[ERROR] No Results CSV found in {output_dir}")
        print("  Make sure you applied the patch to src/utils/file.py")
        sys.exit(1)

    csv_path = matches[0]
    print(f"\n  CSV saved: {csv_path}")
    return csv_path


# ════════════════════════════════════════════════════════════════
# STEP 3 — PARSE CSV
# ════════════════════════════════════════════════════════════════

def parse_omr_csv(csv_path):
    """Read OMRChecker CSV → {1: 'C', 2: 'A', ...} for Q1–Q150."""
    answers = {}
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not any(v.strip() for v in row.values()):
                continue
            if not row.get('q001', '').strip():
                continue
            for key, val in row.items():
                key = key.strip().lower()
                if key.startswith('q') and key[1:].isdigit():
                    answers[int(key[1:])] = val.strip().upper()
            break
    return answers


# ════════════════════════════════════════════════════════════════
# STEP 4 — CHECK ANSWERS
# ════════════════════════════════════════════════════════════════

def check_section(candidate_answers, answer_key, start_q, end_q):
    """
    Compare candidate answers against key for a range of questions.
    Z in key = all options correct, always full mark.
    Returns (score, total, details_list)
    """
    score = 0
    details = []
    for q in range(start_q, end_q + 1):
        correct_num = answer_key.get(q)
        if correct_num is None:
            continue
        user_letter = candidate_answers.get(q, '')
        user_num    = LETTER_TO_NUM.get(user_letter, '')

        if correct_num == 'Z':
            score += 1
            status = 'bonus'
        elif not user_num:
            status = 'blank'
        elif user_num == correct_num:
            score += 1
            status = 'correct'
        else:
            status = 'wrong'

        details.append({
            'q':       q,
            'you':     user_letter or '—',
            'correct': NUM_TO_LETTER.get(correct_num, correct_num),
            'status':  status,
        })

    return score, end_q - start_q + 1, details


def check_answers(candidate_answers, info):
    """Run all three sections and return results dict."""
    subj_key = ANSWER_KEYS[info['subject_key']][info['subject_set']]

    lang1_full = ANSWER_KEYS['languages'][info['lang1_label']][info['lang1_set']]
    lang2_full = ANSWER_KEYS['languages'][info['lang2_label']][info['lang2_set']]

    # Slice language keys to their correct ranges
    lang1_key = {q: v for q, v in lang1_full.items() if 91  <= q <= 120}
    lang2_key = {q: v for q, v in lang2_full.items() if 121 <= q <= 150}

    r1 = check_section(candidate_answers, subj_key,  1,   90)
    r2 = check_section(candidate_answers, lang1_key, 91,  120)
    r3 = check_section(candidate_answers, lang2_key, 121, 150)

    return r1, r2, r3


# ════════════════════════════════════════════════════════════════
# STEP 5 — DISPLAY RESULTS
# ════════════════════════════════════════════════════════════════

STATUS_ICON = {
    'correct': '✓',
    'wrong':   '✗',
    'blank':   '—',
    'bonus':   '★',
}

def print_results(info, r1, r2, r3):
    s1, t1, d1 = r1
    s2, t2, d2 = r2
    s3, t3, d3 = r3
    total = s1 + s2 + s3

    print("\n" + "="*55)
    print("               RESULT CARD")
    print("="*55)
    print(f"  Subject   : {info['subject_label']} ({info['subject_set']})")
    print(f"  Language 1: {info['lang1_label']} ({info['lang1_set']})  →  Q91–120")
    print(f"  Language 2: {info['lang2_label']} ({info['lang2_set']})  →  Q121–150")
    print("─"*55)
    print(f"  {'Section':<30} {'Score':>7}  {'%':>6}")
    print("─"*55)
    print(f"  {'CDP + ' + info['subject_label']:<30} {s1:>3}/{t1:<3}  {s1/t1*100:>5.1f}%")
    print(f"  {'Language 1 (' + info['lang1_label'] + ')':<30} {s2:>3}/{t2:<3}  {s2/t2*100:>5.1f}%")
    print(f"  {'Language 2 (' + info['lang2_label'] + ')':<30} {s3:>3}/{t3:<3}  {s3/t3*100:>5.1f}%")
    print("─"*55)
    print(f"  {'TOTAL':<30} {total:>3}/150  {total/150*100:>5.1f}%")
    print("="*55)

    if total >= 90:
        print(f"\n  RESULT:  ✓ PASSED  ({total}/150 ≥ 90)")
    else:
        print(f"\n  RESULT:  ✗ NOT PASSED  ({total}/150 — need {90 - total} more)")

    # ── Question-wise breakdown ───────────────────────────────
    print()
    show = input("  Show question-wise breakdown? (y/n): ").strip().lower()
    if show != 'y':
        return

    sections = [
        (f"Q1–90 · CDP + {info['subject_label']} ({info['subject_set']})", d1),
        (f"Q91–120 · Language 1: {info['lang1_label']} ({info['lang1_set']})", d2),
        (f"Q121–150 · Language 2: {info['lang2_label']} ({info['lang2_set']})", d3),
    ]

    for title, details in sections:
        correct_count = sum(1 for d in details if d['status'] in ('correct', 'bonus'))
        print(f"\n  ── {title}  [{correct_count}/{len(details)}] ──")
        print(f"  {'Q#':<6} {'You':>4}  {'Key':>4}  {'':>2}")
        print(f"  {'─'*28}")
        for d in details:
            icon = STATUS_ICON[d['status']]
            # Highlight wrong answers
            note = f"  ← {d['correct']}" if d['status'] == 'wrong' else ''
            print(f"  Q{d['q']:<5} {d['you']:>4}  {d['correct']:>4}  {icon}{note}")


# ════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════

def main():
    # 1. Collect inputs from user
    info = collect_inputs()

    # 2. Run OMRChecker
    csv_path = run_omrchecker(info['image_path'])

    # 3. Parse CSV
    print("\n  Parsing answers from CSV...")
    candidate_answers = parse_omr_csv(csv_path)
    if not candidate_answers:
        print("[ERROR] No answers found in CSV. Something went wrong with OMR scanning.")
        sys.exit(1)
    print(f"  Parsed {len(candidate_answers)} answers.")

    # 4. Check answers
    r1, r2, r3 = check_answers(candidate_answers, info)

    # 5. Display results
    print_results(info, r1, r2, r3)


if __name__ == "__main__":
    main()