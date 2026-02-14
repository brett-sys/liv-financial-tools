#!/usr/bin/env python3
"""
Underwriting Risk Assessment Tool
Enter client factors → see which carriers likely approve and at what rating.
"""

import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

try:
    from PIL import Image, ImageTk
except ImportError:
    Image = ImageTk = None

DB_PATH = Path(__file__).resolve().parent / "underwriting.db"
LOGO_PATH = Path(__file__).resolve().parent / "assets" / "livfinancial.webp"


def init_db():
    """Create database and tables if they don't exist."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS carriers (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            product_type TEXT DEFAULT 'IUL',
            bmi_min REAL,
            bmi_max_standard REAL,
            bmi_max_table2 REAL,
            bmi_max_table4 REAL,
            bmi_max_table6 REAL,
            bmi_max_table8 REAL,
            min_age INTEGER,
            max_age INTEGER,
            tobacco_standard INTEGER DEFAULT 0,
            tobacco_table2 INTEGER DEFAULT 1,
            tobacco_decline INTEGER DEFAULT 0,
            diabetes_ok INTEGER DEFAULT 0,
            hypertension_ok INTEGER DEFAULT 1,
            cancer_history_years INTEGER DEFAULT 10,
            dui_years_standard INTEGER DEFAULT 10,
            dui_years_table INTEGER DEFAULT 5,
            notes TEXT
        )
    """)

    # Add new columns for existing DBs
    for col in ["bmi_min", "bmi_max_table6", "bmi_max_table8"]:
        try:
            cur.execute(f"ALTER TABLE carriers ADD COLUMN {col} REAL")
        except sqlite3.OperationalError:
            pass
    try:
        cur.execute("ALTER TABLE carriers ADD COLUMN guaranteed_issue INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass

    # Height/weight build table for exact carrier limits (from chart)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS carrier_build (
            id INTEGER PRIMARY KEY,
            carrier_id INTEGER NOT NULL,
            height_inches INTEGER NOT NULL,
            w_standard INTEGER,
            w_table2 INTEGER,
            w_table4 INTEGER,
            w_table6 INTEGER,
            w_table8 INTEGER,
            w_table10 INTEGER,
            FOREIGN KEY (carrier_id) REFERENCES carriers(id)
        )
    """)

    # Knockouts & declinable conditions
    cur.execute("""
        CREATE TABLE IF NOT EXISTS conditions (
            id INTEGER PRIMARY KEY,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            category TEXT NOT NULL CHECK (category IN ('knockout', 'declinable'))
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS carrier_conditions (
            carrier_id INTEGER NOT NULL,
            condition_code TEXT NOT NULL,
            action TEXT NOT NULL CHECK (action IN ('decline', 'table', 'ok')),
            PRIMARY KEY (carrier_id, condition_code),
            FOREIGN KEY (carrier_id) REFERENCES carriers(id)
        )
    """)

    # Remove sample carriers if present
    cur.execute("DELETE FROM carrier_conditions WHERE carrier_id IN (SELECT id FROM carriers WHERE name LIKE '%(Sample)%')")
    cur.execute("DELETE FROM carrier_build WHERE carrier_id IN (SELECT id FROM carriers WHERE name LIKE '%(Sample)%')")
    cur.execute("DELETE FROM carriers WHERE name LIKE '%(Sample)%'")

    cur.execute("SELECT COUNT(*) FROM carriers")
    if cur.fetchone()[0] == 0:
        pass  # Real carriers added below

    # Add National Life from UW guide if not present
    cur.execute("SELECT id FROM carriers WHERE name = 'National Life (Permanent)' LIMIT 1")
    nl_row = cur.fetchone()
    if nl_row is None:
        _add_national_life(cur)
    else:
        # Ensure build chart exists even if carrier was added before
        cur.execute("SELECT 1 FROM carrier_build WHERE carrier_id=? LIMIT 1", (nl_row[0],))
        if cur.fetchone() is None:
            _add_national_life_build(cur, nl_row[0])

    # Add Transamerica from height/weight charts if not present
    cur.execute("SELECT 1 FROM carriers WHERE name = 'Transamerica (FFIUL)' LIMIT 1")
    if cur.fetchone() is None:
        _add_transamerica(cur)

    # Add Mutual of Omaha IUL Express if not present
    cur.execute("SELECT 1 FROM carriers WHERE name = 'Mutual of Omaha (IUL Express)' LIMIT 1")
    if cur.fetchone() is None:
        _add_mutual_of_omaha(cur)

    # Add Americo Instant Decision IUL if not present
    cur.execute("SELECT 1 FROM carriers WHERE name = 'Americo (Instant Decision IUL)' LIMIT 1")
    if cur.fetchone() is None:
        _add_americo(cur)

    # Add Ethos (Ameritas) IUL if not present
    cur.execute("SELECT 1 FROM carriers WHERE name = 'Ethos (Ameritas IUL)' LIMIT 1")
    if cur.fetchone() is None:
        _add_ethos_ameritas(cur)

    # Add Term carriers from UW guides if not present
    cur.execute("SELECT 1 FROM carriers WHERE name = 'Ethos Term' LIMIT 1")
    if cur.fetchone() is None:
        _add_term_carriers(cur)
        # Remove old sample term carriers (replaced by real UW guide data)
        for old in ("Banner Life (Term)", "Protective (Term)", "Lincoln (Term)"):
            cur.execute("DELETE FROM carrier_conditions WHERE carrier_id IN (SELECT id FROM carriers WHERE name=?)", (old,))
            cur.execute("DELETE FROM carriers WHERE name=?", (old,))

    # Add Final Expense carriers from UW guides if not present
    cur.execute("SELECT 1 FROM carriers WHERE name = 'Accendo (Final Expense)' LIMIT 1")
    if cur.fetchone() is None:
        _add_fe_carriers(cur)
        for old in ("Gerber (Final Expense)", "AIG (Final Expense)", "Transamerica (Final Expense)"):
            cur.execute("DELETE FROM carrier_conditions WHERE carrier_id IN (SELECT id FROM carriers WHERE name=?)", (old,))
            cur.execute("DELETE FROM carriers WHERE name=?", (old,))

    # Migration: ensure bmi_min set for carriers that need it
    cur.execute("UPDATE carriers SET bmi_min=18.0 WHERE name='Ethos (Ameritas IUL)'")
    cur.execute("UPDATE carriers SET bmi_min=17.7 WHERE name='Americo (Instant Decision IUL)'")

    _seed_conditions(cur)
    conn.commit()
    conn.close()


def _seed_conditions(cur):
    """Seed knockouts and declinable conditions (common impairments guide)."""
    # condition_code, name, category (knockout = typically decline; declinable = table or decline)
    conditions_data = [
        # Knockouts
        ("hiv", "HIV/AIDS", "knockout"),
        ("organ_transplant", "Organ / bone marrow transplant", "knockout"),
        ("als_ms_parkinsons", "ALS / MS / Parkinson's", "knockout"),
        ("dialysis", "Current dialysis / renal failure", "knockout"),
        ("drug_abuse", "Drug/substance abuse (current)", "knockout"),
        ("prior_decline", "Prior life insurance decline", "knockout"),
        ("metastatic_cancer", "Metastatic or recurrent cancer", "knockout"),
        ("mental_incapacity", "Mental incapacity", "knockout"),
        ("paralysis", "Paralysis", "knockout"),
        ("sickle_cell", "Sickle cell anemia", "knockout"),
        # Declinable
        ("abnormal_heart_rhythm", "Abnormal/irregular heart rhythm", "declinable"),
        ("alcohol_drug_treatment", "Alcohol or drug treatment history", "declinable"),
        ("amputation_disease", "Amputation caused by disease", "declinable"),
        ("asthma_severe", "Asthma (chronic or severe)", "declinable"),
        ("bipolar_schizophrenia", "Bipolar / schizophrenia / major depression", "declinable"),
        ("cardiomyopathy", "Cardiomyopathy", "declinable"),
        ("cerebral_palsy", "Cerebral palsy", "declinable"),
        ("chronic_kidney", "Chronic kidney disease", "declinable"),
        ("chf", "Congestive heart failure (CHF)", "declinable"),
        ("crohns_colitis", "Crohn's disease / ulcerative colitis", "declinable"),
        ("coronary_disease", "Coronary disease / heart attack / heart surgery", "declinable"),
        ("copd", "COPD / chronic bronchitis / emphysema / cystic fibrosis", "declinable"),
        ("cancer", "Cancer (see years ago for history)", "declinable"),
        ("defibrillator", "Defibrillator", "declinable"),
        ("diabetes_complications", "Diabetes with complications (retinopathy, nephropathy, neuropathy)", "declinable"),
        ("heart_disease", "Heart disease or surgery", "declinable"),
        ("hepatitis_bc", "Hepatitis B or C", "declinable"),
        ("hodgkins", "Hodgkin's disease", "declinable"),
        ("liver_disease", "Liver disease / cirrhosis", "declinable"),
        ("leukemia", "Leukemia", "declinable"),
        ("lymphoma", "Lymphoma", "declinable"),
        ("melanoma", "Melanoma", "declinable"),
        ("muscular_dystrophy", "Muscular dystrophy / neurological disorders", "declinable"),
        ("pacemaker", "Pacemaker", "declinable"),
        ("pancreatitis", "Pancreatitis (chronic or alcohol-related)", "declinable"),
        ("pvd_pad", "Peripheral vascular disease (PVD/PAD)", "declinable"),
        ("kidney_disease", "Renal insufficiency / kidney disease", "declinable"),
        ("rheumatoid_arthritis", "Rheumatoid arthritis (moderate/severe)", "declinable"),
        ("scleroderma", "Scleroderma", "declinable"),
        ("stroke_tia", "Stroke or mini-stroke (TIA)", "declinable"),
        ("seizure", "Seizure disorder", "declinable"),
        ("sleep_apnea", "Sleep apnea (untreated/severe)", "declinable"),
    ]
    for code, name, cat in conditions_data:
        cur.execute(
            "INSERT OR REPLACE INTO conditions (code, name, category) VALUES (?, ?, ?)",
            (code, name, cat),
        )

    # Get carrier IDs by name
    cur.execute("SELECT id, name FROM carriers")
    carriers_by_id = {r[0]: r[1] for r in cur.fetchall()}

    knockout_codes = [c[0] for c in conditions_data if c[2] == "knockout"]
    declinable_codes = [c[0] for c in conditions_data if c[2] == "declinable"]

    declinable_rules = [
        ("Americo (Instant Decision IUL)", "decline"),
        ("Mutual of Omaha (IUL Express)", "decline"),
        ("National Life (Permanent)", "table"),
        ("Transamerica (FFIUL)", "table"),
        ("Ethos (Ameritas IUL)", "table"),
        ("Ethos Term", "table"),
        ("InstaBrain Term", "decline"),
        ("Ladder (Term)", "table"),
        ("Family Freedom Term", "table"),
        ("TruStage Term", "decline"),
        ("Accendo (Final Expense)", "table"),
        ("Americo Eagle Select", "table"),
        ("Fidelity Life RAPIDecision GI", "ok"),
        ("Royal Neighbors Ensured Legacy", "table"),
        ("Living Promise (Final Expense)", "table"),
    ]
    name_to_id = {v: k for k, v in carriers_by_id.items()}
    for carrier_name, declinable_action in declinable_rules:
        cid = name_to_id.get(carrier_name)
        if not cid:
            continue
        for code in knockout_codes:
            cur.execute(
                "INSERT OR REPLACE INTO carrier_conditions (carrier_id, condition_code, action) VALUES (?, ?, 'decline')",
                (cid, code),
            )
        for code in declinable_codes:
            cur.execute(
                "INSERT OR REPLACE INTO carrier_conditions (carrier_id, condition_code, action) VALUES (?, ?, ?)",
                (cid, code, declinable_action),
            )


def _add_national_life(cur):
    """Add National Life from General Underwriting Guide (Permanent Products).
    Build: Elite <27.1, Preferred <29.9, Select <32.7, Express Std1 <37.5, Std2 <42.5, Table8 <46.5.
    """
    cur.execute("""
        INSERT INTO carriers (name, product_type,
            bmi_min, bmi_max_standard, bmi_max_table2, bmi_max_table4, bmi_max_table6, bmi_max_table8,
            min_age, max_age,
            tobacco_standard, tobacco_table2, tobacco_decline,
            diabetes_ok, hypertension_ok, cancer_history_years,
            dui_years_standard, dui_years_table, notes)
        VALUES ('National Life (Permanent)', 'IUL',
            18.5, 29.9, 32.7, 37.5, 42.5, 46.5,
            18, 85,
            1, 1, 0,
            0, 2, 5,
            10, 5,
            'SummitLife/PeakLife/FlexLife. Elite/Preferred/Select build. Diabetes decline. HTN ok if controlled. DUI: 5yr table, 10yr std. Cancer 3-5yr contact UW.')
    """)
    # Add exact height/weight build from chart (page 29, upper bounds per class)
    cid = cur.lastrowid
    _add_national_life_build(cur, cid)


def _add_national_life_build(cur, carrier_id):
    """National Life Permanent Products build chart (page 29). Upper bound lbs per height.
    Elite, Preferred, Select, Express Std1, Express Std2, Table8.
    """
    # height_inches, w_standard(Elite), w_table2(Pref), w_table4(Select), w_table6(Expr1), w_table8(Expr2), w_table10(Table8)
    data = [
        (56, 120, 133, 145, 167, 189, 207),   # 4'8"
        (57, 125, 138, 151, 173, 196, 214),   # 4'9"
        (58, 129, 143, 156, 179, 203, 222),   # 4'10"
        (59, 134, 148, 161, 185, 210, 230),   # 4'11"
        (60, 138, 153, 167, 191, 217, 238),   # 5'0"
        (61, 143, 158, 173, 198, 224, 246),   # 5'1"
        (62, 148, 163, 178, 205, 232, 254),   # 5'2"
        (63, 152, 168, 184, 211, 239, 262),   # 5'3"
        (64, 157, 174, 190, 218, 247, 270),   # 5'4"
        (65, 162, 179, 196, 225, 255, 279),   # 5'5"
        (66, 167, 185, 202, 232, 263, 288),   # 5'6"
        (67, 172, 190, 208, 239, 271, 296),   # 5'7"
        (68, 177, 196, 215, 246, 279, 305),   # 5'8"
        (69, 183, 202, 221, 253, 287, 314),   # 5'9"
        (70, 188, 208, 227, 261, 296, 324),   # 5'10"
        (71, 194, 214, 234, 268, 304, 333),   # 5'11"
        (72, 199, 220, 241, 276, 313, 342),   # 6'0"
        (73, 205, 226, 247, 284, 322, 352),   # 6'1"
        (74, 211, 232, 254, 292, 330, 362),   # 6'2"
        (75, 216, 239, 261, 299, 339, 371),   # 6'3"
        (76, 222, 245, 268, 308, 349, 381),   # 6'4"
        (77, 228, 252, 275, 316, 358, 392),   # 6'5"
        (78, 234, 258, 282, 324, 367, 402),   # 6'6"
        (79, 240, 265, 290, 332, 377, 412),   # 6'7"
        (80, 246, 272, 297, 341, 386, 423),   # 6'8"
    ]
    for row in data:
        cur.execute(
            """INSERT INTO carrier_build (carrier_id, height_inches, w_standard, w_table2, w_table4, w_table6, w_table8, w_table10)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (carrier_id, row[0], row[1], row[2], row[3], row[4], row[5], row[6]),
        )


def _add_transamerica(cur):
    """Add Transamerica from height/weight charts (Female & Male, Ages 18-70).
    Charts use height+weight; converted to approximate BMI. Preferred Elite ~28,
    Preferred Plus ~31, Preferred ~33, Standard Plus ~36, Standard ~40.
    Separate charts for 71+ and gender - tool uses blended approximate values.
    """
    cur.execute("""
        INSERT INTO carriers (name, product_type,
            bmi_min, bmi_max_standard, bmi_max_table2, bmi_max_table4, bmi_max_table6, bmi_max_table8,
            min_age, max_age,
            tobacco_standard, tobacco_table2, tobacco_decline,
            diabetes_ok, hypertension_ok, cancer_history_years,
            dui_years_standard, dui_years_table, notes)
        VALUES ('Transamerica (FFIUL)', 'IUL',
            NULL, 28.2, 31.0, 33.4, 36.0, 40.0,
            18, 85,
            1, 1, 0,
            2, 2, 10, 10, 5,
            'FFIUL/TFLIC FFIUL. Ht/Wt charts-Ages 18-70. Preferred Elite/Plus/Preferred/Std Plus/Std. 71+ and gender differ-see chart.')
    """)


def _add_mutual_of_omaha(cur):
    """Add Mutual of Omaha IUL Express from Underwriting IUL MOO guide.
    Build chart: Standard max ~42 BMI, Table 2 (multiple impairments) ~38 BMI.
    Simplified issue. Diabetes decline. HTN treatment allowed. Tobacco 12mo. DUI 5yr.
    """
    cur.execute("""
        INSERT INTO carriers (name, product_type,
            bmi_min, bmi_max_standard, bmi_max_table2, bmi_max_table4, bmi_max_table6, bmi_max_table8,
            min_age, max_age,
            tobacco_standard, tobacco_table2, tobacco_decline,
            diabetes_ok, hypertension_ok, cancer_history_years,
            dui_years_standard, dui_years_table, notes)
        VALUES ('Mutual of Omaha (IUL Express)', 'IUL',
            NULL, 42.0, 38.0, NULL, NULL, NULL,
            18, 75,
            0, 1, 0,
            0, 2, 10, 5, 5,
            'IUL Express. Simplified issue $25K-$300K (18-50). Diabetes decline. HTN ok. DUI 5yr. Table 2 build=multiple impairments. Table 4+ or prior decline=ineligible.')
    """)


def _add_americo(cur):
    """Add Americo Instant Decision IUL from IULAgentGuide.
    Build: height/weight chart, max ~42 BMI. No substandard. Non-nicotine 24mo.
    Ages 18-65. $50K-$450K non-medical.
    """
    cur.execute("""
        INSERT INTO carriers (name, product_type,
            bmi_min, bmi_max_standard, bmi_max_table2, bmi_max_table4, bmi_max_table6, bmi_max_table8,
            min_age, max_age,
            tobacco_standard, tobacco_table2, tobacco_decline,
            diabetes_ok, hypertension_ok, cancer_history_years,
            dui_years_standard, dui_years_table, notes)
        VALUES ('Americo (Instant Decision IUL)', 'IUL',
            17.7, 42.0, NULL, NULL, NULL, NULL,
            18, 65,
            0, 1, 0,
            0, 2, 10, 10, 5,
            'Instant Decision IUL. No substandard. Non-nicotine 24mo. Non-med $50K-$450K. Build chart ht/wt. Knock-out health questions.')
    """)


def _add_ethos_ameritas(cur):
    """Add Ethos IUL (Ameritas) from IUL Underwriting One-Pager.
    BMI 18-49. Diabetes OK if age 35+, no complications, A1C ≤9.5, BMI ≤41.49.
    DUI 5yr. Cancer 10yr. BP limits by age.
    """
    cur.execute("""
        INSERT INTO carriers (name, product_type,
            bmi_min, bmi_max_standard, bmi_max_table2, bmi_max_table4, bmi_max_table6, bmi_max_table8,
            min_age, max_age,
            tobacco_standard, tobacco_table2, tobacco_decline,
            diabetes_ok, hypertension_ok, cancer_history_years,
            dui_years_standard, dui_years_table, notes)
        VALUES ('Ethos (Ameritas IUL)', 'IUL',
            18.0, 49.0, 41.5, NULL, NULL, NULL,
            18, 70,
            0, 1, 0,
            1, 2, 10, 5, 5,
            'Ethos IUL. BMI 18-49. Diabetes: age 35+, no complications, A1C ≤9.5, BMI ≤41.49. DUI 5yr. Cancer 10yr. BP limits by age.')
    """)


def _add_term_carriers(cur):
    """Add Term carriers from FFL-LIV underwriting guides (2023 Grid, Ethos, InstaBrain, Ladder, Family Freedom)."""
    carriers = [
        # Ethos Term (TLE/IULE) - from 2023 Term Grid. Prime=$2M, Spectrum=$500K, Select=$150K. DUI 5yr.
        ("Ethos Term", "Term", 18.0, 30.0, 32.0, 37.0, 42.0, 46.5, 18, 60, 1, 1, 0, 1, 2, 10, 10, 5,
         "Ethos TLE/IULE. Prime best, Spectrum mod, Select highest risk. Many conditions→Select or FE. DUI 5yr. Use online quoting for ht/wt."),
        # InstaBrain Term (Fidelity Life) - from InstaBrain guide. NT: P+ 18-28 BMI, P 29-30, Std 31-32, StdEx 33-37. Build chart.
        ("InstaBrain Term", "Term", 18.0, 28.0, 30.0, 32.0, 37.0, 46.0, 18, 60, 0, 1, 0, 0, 2, 10, 5, 5,
         "InstaBrain/Fidelity Life. NT: P+ 18-28, P 29-30, Std 31-32, StdEx 33-37. Ages 18-60. Diabetes/insulin/cancer decline. DUI 5yr."),
        # Ladder (Prosperity LadderLife / S.USA) - from Ladder guide. P+ 18-28, P 29-30, Std+ 31-32, Std 33-37. DUI 5yr.
        ("Ladder (Term)", "Term", 18.0, 28.0, 30.0, 32.0, 37.0, 46.0, 20, 60, 0, 1, 0, 2, 2, 10, 10, 5,
         "Prosperity LadderLife. P+ 18-28, P 29-30, Std+ 31-32, Std 33-37. No DUI/revocation 5yr. Diabetes type 2 OK if controlled."),
        # Family Freedom Term (Transamerica) - from 2023 Grid. 18-75, $50K-$500K simplified. Many conditions→Select.
        ("Family Freedom Term", "Term", None, 40.0, 42.0, 45.0, None, None, 18, 75, 0, 1, 0, 2, 2, 5, 5, 3,
         "Transamerica Family Freedom. 10-30yr level term. $50K-$500K simplified. Living benefit riders. Many conditions→Select or decline."),
        # TruStage Term - from 2023 Grid. Strictest. Home Mortgage Series, Term Made Simple.
        ("TruStage Term", "Term", None, 35.0, 38.0, 40.0, None, None, 18, 70, 0, 1, 0, 0, 2, 10, 10, 5,
         "TruStage. Home Mortgage Series / Term Made Simple. Strict UW. Many conditions ineligible. DUI 10yr."),
    ]
    for c in carriers:
        cur.execute(
            """INSERT INTO carriers (name, product_type,
               bmi_min, bmi_max_standard, bmi_max_table2, bmi_max_table4, bmi_max_table6, bmi_max_table8,
               min_age, max_age,
               tobacco_standard, tobacco_table2, tobacco_decline,
               diabetes_ok, hypertension_ok, cancer_history_years,
               dui_years_standard, dui_years_table, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            c,
        )
    # InstaBrain build chart (from guide p.8)
    instabrain_id = None
    for row in cur.execute("SELECT id FROM carriers WHERE name='InstaBrain Term' LIMIT 1"):
        instabrain_id = row[0]
        break
    if instabrain_id:
        _add_instabrain_build(cur, instabrain_id)


def _add_instabrain_build(cur, carrier_id):
    """InstaBrain Term build chart (Fidelity Life). Preferred+, Preferred, Standard, Standard Extra max weights."""
    data = [
        (56, 83, 135, 150, 161, 179), (57, 86, 140, 155, 167, 185), (58, 90, 144, 160, 172, 191),
        (59, 93, 149, 165, 178, 198), (60, 96, 153, 170, 185, 205), (61, 99, 158, 175, 191, 212),
        (62, 102, 162, 180, 197, 219), (63, 106, 167, 186, 203, 226), (64, 109, 173, 192, 210, 233),
        (65, 112, 178, 198, 216, 240), (66, 116, 184, 204, 223, 248), (67, 119, 189, 210, 230, 255),
        (68, 123, 194, 216, 237, 263), (69, 127, 201, 223, 244, 271), (70, 130, 206, 229, 251, 279),
        (71, 134, 212, 236, 258, 287), (72, 138, 219, 243, 266, 295), (73, 142, 224, 249, 273, 303),
        (74, 146, 230, 256, 281, 312), (75, 150, 237, 263, 288, 320), (76, 154, 243, 270, 296, 329),
        (77, 158, 249, 277, 303, 337), (78, 162, 257, 285, 311, 346), (79, 166, 263, 292, 320, 355),
        (80, 170, 270, 300, 328, 364), (81, 175, 278, 309, 336, 373), (82, 179, 286, 318, 345, 383),
    ]
    for row in data:
        hi, _min, pplus, pref, std, stdextra = row
        cur.execute(
            """INSERT INTO carrier_build (carrier_id, height_inches, w_standard, w_table2, w_table4, w_table6)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (carrier_id, hi, pplus, pref, std, stdextra),
        )


def _add_fe_carriers(cur):
    """Add Final Expense carriers from FFL-LIV UW guides (Final Expense Grid, Eagle Select, RAPIDecision GI, Royal Neighbors)."""
    # (name, product_type, bmi_min, bmi_max_std, bmi_max_t2, bmi_max_t4, bmi_max_t6, bmi_max_t8,
    #  min_age, max_age, tobacco_std, tobacco_t2, tobacco_decline,
    #  diabetes_ok, htn_ok, cancer_yrs, dui_std, dui_tbl, notes, guaranteed_issue)
    carriers = [
        # Accendo (Aetna/CVS) - from Final Expense Grid. Very lenient. Many "Not asked - Allowed". GI for severe.
        ("Accendo (Final Expense)", "Final Expense", None, 50.0, 52.0, 55.0, None, None, 40, 89, 0, 1, 0, 2, 2, 2, 5, 2,
         "Accendo/Aetna FEX. $2K-$50K. Ages 40-89. Level & Modified. Many conditions allowed or GI. Diabetes/HTN OK.", 0),
        # Americo Eagle Select - 3 tiers. 40-85, up to $40K. Fast POS.
        ("Americo Eagle Select", "Final Expense", None, 45.0, 48.0, 52.0, None, None, 40, 85, 0, 1, 0, 2, 2, 5, 5, 3,
         "Americo Eagle Select. Ages 40-85. Up to $40K. 3 tiers. Quit Smoking Advantage. Instant decision.", 0),
        # Fidelity Life RAPIDecision GI - Guaranteed Issue. 50-85, $5K-$25K. No underwriting.
        ("Fidelity Life RAPIDecision GI", "Final Expense", None, 60.0, 60.0, 60.0, None, None, 50, 85, 0, 1, 0, 2, 2, 0, 10, 0,
         "RAPIDecision Guaranteed Issue. Ages 50-85. $5K-$25K. No underwriting. Graded benefit yrs 1-3.", 1),
        # Royal Neighbors Ensured Legacy - Preferred, Standard, GDB, GI. From risk assessment chart.
        ("Royal Neighbors Ensured Legacy", "Final Expense", None, 42.0, 45.0, 48.0, None, None, 18, 85, 0, 1, 0, 2, 2, 5, 5, 3,
         "Ensured Legacy. Preferred/Standard/GDB/GI tiers. Diabetes no insulin OK. Many conditions→GDB or GI.", 0),
        # Living Promise - from Final Expense Grid. One of the grid products.
        ("Living Promise (Final Expense)", "Final Expense", None, 44.0, 47.0, 50.0, None, None, 18, 85, 0, 1, 0, 2, 2, 4, 5, 2,
         "Living Promise from FE Grid. Graded for many conditions. Cancer >4yr allowed. DUI 2yr.", 0),
    ]
    for c in carriers:
        vals = c[:-1]  # exclude guaranteed_issue
        gi = c[-1]
        cur.execute(
            """INSERT INTO carriers (name, product_type,
               bmi_min, bmi_max_standard, bmi_max_table2, bmi_max_table4, bmi_max_table6, bmi_max_table8,
               min_age, max_age,
               tobacco_standard, tobacco_table2, tobacco_decline,
               diabetes_ok, hypertension_ok, cancer_history_years,
               dui_years_standard, dui_years_table, notes, guaranteed_issue)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (*vals, gi),
        )


def get_carriers(product_type: str | None = None):
    """Return carriers from DB, optionally filtered by product_type (IUL, Term, Final Expense)."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    if product_type:
        cur.execute("SELECT * FROM carriers WHERE product_type=? ORDER BY name", (product_type,))
    else:
        cur.execute("SELECT * FROM carriers ORDER BY name")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_conditions():
    """Return all conditions (knockouts and declinable), grouped by category."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT code, name, category FROM conditions ORDER BY category, name")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_carrier_conditions() -> dict[int, dict[str, str]]:
    """Return {carrier_id: {condition_code: action}} for all carriers."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT carrier_id, condition_code, action FROM carrier_conditions")
    rows = cur.fetchall()
    conn.close()
    result: dict[int, dict[str, str]] = {}
    for cid, code, action in rows:
        if cid not in result:
            result[cid] = {}
        result[cid][code] = action
    return result


def get_build_for_carrier(carrier_id: int, height_inches: float) -> dict | None:
    """Get height/weight build row for carrier. Returns nearest height row."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM carrier_build WHERE carrier_id=? ORDER BY abs(height_inches - ?) LIMIT 1",
        (carrier_id, height_inches),
    )
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def assess(client: dict, carriers: list) -> list[dict]:
    """
    Assess client against each carrier. Returns list of {carrier, rating, notes, declined}.
    Approved carriers have declined=False. Declined carriers have declined=True and rating=None.
    """
    carrier_cond = get_carrier_conditions()
    cond_names = {c["code"]: c["name"] for c in get_conditions()}
    results = []
    for c in carriers:
        cc = carrier_cond.get(c["id"], {})
        rating, notes = _evaluate_one(client, c, cc, cond_names)
        results.append({
            "carrier": c["name"],
            "rating": rating,
            "notes": notes,
            "declined": rating is None,
        })
    approved = [r for r in results if not r["declined"]]
    declined = [r for r in results if r["declined"]]
    return sorted(approved, key=lambda x: _rating_order(x["rating"])) + declined


def _rating_order(r: str) -> int:
    """Lower = better. Standard=0, Table2=1, etc. Includes NL, InstaBrain, Ethos tiers."""
    order = {
        "Standard": 0, "Elite": 0, "Preferred Plus": 0,
        "Table 2": 1, "Preferred": 1,
        "Table 4": 2, "Select": 2, "Graded": 2,
        "Table 6": 3, "Express Std1": 3, "Standard Extra": 3,
        "Table 8": 4, "Express Std2": 4,
        "Decline": 99,
    }
    return order.get(r, 99)


def _evaluate_one(client: dict, carrier: dict, carrier_conditions: dict[str, str] | None = None, cond_names: dict[str, str] | None = None) -> tuple[str | None, str]:
    """Evaluate client vs carrier. Returns (rating, notes) or (None, notes) if decline."""
    notes = []
    cc = carrier_conditions or {}
    cond_names = cond_names or {}

    # Guaranteed Issue - no underwriting, all approved (graded benefit)
    if carrier.get("guaranteed_issue"):
        age = client.get("age")
        if age is not None and carrier.get("min_age") and age < carrier["min_age"]:
            return None, "Age below minimum"
        if age is not None and carrier.get("max_age") and age > carrier["max_age"]:
            return None, "Age above maximum"
        return "Graded", "Guaranteed Issue – graded benefit years 1–3"

    # Age
    age = client.get("age")
    if age is not None:
        if carrier.get("min_age") and age < carrier["min_age"]:
            return None, "Age below minimum"
        if carrier.get("max_age") and age > carrier["max_age"]:
            return None, "Age above maximum"

    bmi = client.get("bmi")
    height_inches = client.get("height")
    weight = client.get("weight")

    # Min BMI check (e.g. Ethos 18, Americo 17.7)
    bmi_min = carrier.get("bmi_min")
    if bmi_min is not None and bmi is not None and bmi < bmi_min:
        return None, f"BMI below minimum ({bmi_min})"

    # Build: prefer height/weight chart when available and we have height+weight
    build_rating = None
    build_notes = None
    if height_inches and weight is not None and height_inches > 0:
        build_row = get_build_for_carrier(carrier["id"], height_inches)
        if build_row:
            w = int(weight)
            # Check weight vs limits (best to worst). National Life: Elite→Preferred→Select→Express Std1→Express Std2→Table8
            cname = carrier.get("name", "")
            if build_row.get("w_standard") is not None and w <= build_row["w_standard"]:
                if "National Life" in cname:
                    build_rating, build_notes = "Elite", "Build → Elite"
                elif "InstaBrain" in cname:
                    build_rating, build_notes = "Preferred Plus", "Build → Preferred Plus"
                else:
                    build_rating, build_notes = "Standard", "Build → Standard"
            elif build_row.get("w_table2") is not None and w <= build_row["w_table2"]:
                if "National Life" in cname:
                    build_rating, build_notes = "Preferred", "Build → Preferred"
                elif "InstaBrain" in cname:
                    build_rating, build_notes = "Preferred", "Build → Preferred"
                else:
                    build_rating, build_notes = "Table 2", "Build → Table 2"
            elif build_row.get("w_table4") is not None and w <= build_row["w_table4"]:
                if "National Life" in cname:
                    build_rating, build_notes = "Select", "Build → Select"
                elif "InstaBrain" in cname:
                    build_rating, build_notes = "Standard", "Build → Standard"
                else:
                    build_rating, build_notes = "Table 4", "Build → Table 4"
            elif build_row.get("w_table6") is not None and w <= build_row["w_table6"]:
                if "National Life" in cname:
                    build_rating, build_notes = "Express Std1", "Build → Express Std1"
                elif "InstaBrain" in cname:
                    build_rating, build_notes = "Standard Extra", "Build → Standard Extra"
                else:
                    build_rating, build_notes = "Table 6", "Build → Table 6"
            elif build_row.get("w_table8") is not None and w <= build_row["w_table8"]:
                build_rating = "Express Std2" if "National Life" in cname else "Table 8"
                build_notes = f"Build → {build_rating}"
            elif build_row.get("w_table10") is not None and w <= build_row["w_table10"]:
                build_rating, build_notes = "Table 8", "Build → Table 8"
            else:
                max_w = build_row.get("w_table10") or build_row.get("w_table8") or build_row.get("w_standard")
                return None, f"Build exceeds limits (max {max_w} lbs for height)"

    # BMI fallback when no build chart
    if build_rating is None and bmi is not None:
        max_t8 = carrier.get("bmi_max_table8")
        max_t6 = carrier.get("bmi_max_table6")
        max_t4 = carrier.get("bmi_max_table4")
        max_t2 = carrier.get("bmi_max_table2")
        max_std = carrier.get("bmi_max_standard")
        if max_std and bmi <= max_std:
            pass  # standard possible
        elif max_t2 and bmi <= max_t2:
            notes.append("BMI → Table 2")
        elif max_t4 and bmi <= max_t4:
            notes.append("BMI → Table 4")
        elif max_t6 and bmi <= max_t6:
            notes.append("BMI → Table 6")
        elif max_t8 and bmi <= max_t8:
            notes.append("BMI → Table 8")
        else:
            return None, "BMI exceeds limits"

    if build_notes:
        notes.append(build_notes)

    # Tobacco
    tobacco = client.get("tobacco", False)
    if tobacco:
        if carrier["tobacco_decline"]:
            return None, "Tobacco decline"
        if carrier["tobacco_standard"]:
            notes.append("Tobacco → Standard")
        else:
            notes.append("Tobacco → Table rating")

    # Diabetes
    if client.get("diabetes"):
        if carrier["diabetes_ok"] == 0:
            return None, "Diabetes decline"
        if carrier["diabetes_ok"] == 1:
            notes.append("Diabetes → Table rating")

    # Hypertension
    if client.get("hypertension"):
        if carrier["hypertension_ok"] == 0:
            return None, "Hypertension decline"
        if carrier["hypertension_ok"] == 1:
            notes.append("HTN → Table rating")

    # Cancer history (client value = years since cancer; 999 = none)
    cancer_years = client.get("cancer_history_years")
    if cancer_years is not None and 0 < cancer_years < 999:
        req = carrier.get("cancer_history_years") or 10
        if cancer_years < req:
            return None, f"Cancer history within {req} years"

    # DUI (client value = years ago; 999 = none)
    dui_years = client.get("dui_years_ago")
    if dui_years is not None and dui_years < 999:
        std = carrier.get("dui_years_standard") or 10
        tbl = carrier.get("dui_years_table") or 5
        if dui_years < tbl:
            return None, "DUI too recent"
        if dui_years < std:
            notes.append("DUI → Table rating")

    # Knockouts & declinable conditions (client.conditions = set of condition codes)
    client_conditions = client.get("conditions") or set()
    for code in client_conditions:
        action = cc.get(code)
        if action == "decline":
            name = cond_names.get(code, code)
            return None, f"{name} decline"
        if action == "table":
            name = cond_names.get(code, code)
            notes.append(f"{name} → Table rating")

    # Determine best rating (worst factor wins). Combine build + tobacco/diabetes/htn/dui.
    def _worst_of(a: str | None, b: str | None) -> str:
        if not a:
            return b or "Standard"
        if not b:
            return a
        return a if _rating_order(a) >= _rating_order(b) else b

    worst = build_rating
    if "BMI → Table 8" in notes:
        worst = _worst_of(worst, "Table 8")
    elif "BMI → Table 6" in notes:
        worst = _worst_of(worst, "Table 6")
    elif "BMI → Table 4" in notes:
        worst = _worst_of(worst, "Table 4")
    elif "BMI → Table 2" in notes:
        worst = _worst_of(worst, "Table 2")

    for n in notes:
        if "DUI → Table rating" in n:
            worst = _worst_of(worst, "Table 4")
        elif " → Table rating" in n:
            worst = _worst_of(worst, "Table 2")

    if worst is None:
        worst = "Standard"

    return worst, "; ".join(notes) if notes else "Likely best class"


# LIV Financial theme (matches pdf_generator / livfinancialgroup.com)
LIV = {
    "bg": "#e6f2f5",           # app background
    "panel": "#ffffff",        # cards/panels
    "panel2": "#f5fafc",      # alt panel
    "border": "#d1e2ea",      # borders
    "primary": "#0e7fa6",     # primary blue
    "text": "#123047",        # primary text
    "subtext": "#476072",     # secondary text
    "muted": "#6b7f8f",       # muted
    "success": "#22C55E",     # Standard/approve
    "warn": "#F59E0B",        # Table-rated
    "decline": "#EF4444",     # Decline
    "neutral": "#6b7f8f",     # GI/graded
}

class UnderwritingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Underwriting Risk Assessment")
        self.root.geometry("780x780")
        self.root.configure(bg=LIV["bg"])

        self._apply_theme()
        init_db()
        self._build_ui()

    def _apply_theme(self):
        """Apply LIV Financial theme (matches pdf_generator)."""
        style = ttk.Style()
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure(".", background=LIV["bg"], foreground=LIV["text"])
        style.configure("TFrame", background=LIV["bg"])
        style.configure("TLabel", background=LIV["bg"], foreground=LIV["text"])
        style.configure("TLabelframe", background=LIV["panel"], foreground=LIV["primary"])
        style.configure("TLabelframe.Label", background=LIV["panel"], foreground=LIV["primary"], font=("Helvetica", 10, "bold"))
        style.configure("TCombobox", fieldbackground=LIV["panel"], foreground=LIV["text"])
        style.configure("TCheckbutton", background=LIV["bg"], foreground=LIV["text"])
        style.configure("TButton", background=LIV["primary"], foreground="white")
        style.map("TButton", background=[("active", "#0a6b8c")])
        style.configure("Treeview", background=LIV["panel"], foreground=LIV["text"], fieldbackground=LIV["panel"])
        style.configure("Treeview.Heading", background=LIV["primary"], foreground="white")
        style.configure("Vertical.TScrollbar", background=LIV["panel"])
        self.root.option_add("*Font", "Helvetica 10")

    def _liv_entry(self, parent, **kwargs):
        """Create Entry with LIV styling (blue outline)."""
        e = tk.Entry(parent, bg=LIV["panel"], fg=LIV["text"], insertbackground=LIV["primary"],
                    highlightbackground=LIV["border"], highlightcolor=LIV["primary"], highlightthickness=2,
                    relief=tk.FLAT, font=("Helvetica", 10), **kwargs)
        return e

    def _liv_frame(self, parent, **kwargs):
        """Create Frame with LIV border."""
        f = tk.Frame(parent, bg=LIV["border"], **kwargs)
        inner = tk.Frame(f, bg=LIV["panel"], padx=12, pady=12)
        inner.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        return f, inner

    def _build_ui(self):
        main = ttk.Frame(self.root, padding=20)
        main.pack(fill=tk.BOTH, expand=True)

        # Header with logo and title
        header = tk.Frame(main, bg=LIV["primary"], pady=12, padx=20)
        header.pack(fill=tk.X, pady=(0, 16))
        header_inner = tk.Frame(header, bg=LIV["primary"])
        header_inner.pack(fill=tk.X)
        if Image and ImageTk and LOGO_PATH.exists():
            try:
                img = Image.open(LOGO_PATH)
                img = img.resize((160, 48), Image.LANCZOS)
                self._logo_photo = ImageTk.PhotoImage(img)
                logo_lbl = tk.Label(header_inner, image=self._logo_photo, bg=LIV["primary"])
                logo_lbl.pack(side=tk.LEFT)
            except Exception:
                self._logo_photo = None
        title = tk.Label(header_inner, text="Underwriting Risk Assessment", font=("Helvetica", 18, "bold"),
                        bg=LIV["primary"], fg="white")
        title.pack(side=tk.LEFT, padx=(20, 0))

        # Product type
        f = ttk.Frame(main)
        f.pack(fill=tk.X, pady=(0, 12))
        ttk.Label(f, text="Product type:", width=22, anchor=tk.W).pack(side=tk.LEFT, padx=(0, 8))
        self.product_var = tk.StringVar(value="IUL")
        product_combo = ttk.Combobox(f, textvariable=self.product_var, values=["IUL", "Term", "Final Expense"], state="readonly", width=16)
        product_combo.pack(side=tk.LEFT)

        # Input section
        input_outer, input_frame = self._liv_frame(main)
        ttk.Label(input_frame, text="Client Factors", font=("Helvetica", 11, "bold")).pack(anchor=tk.W, pady=(0, 8))
        input_outer.pack(fill=tk.X, pady=(0, 12))

        f = ttk.Frame(input_frame)
        f.pack(fill=tk.X, pady=2)

        ttk.Label(f, text="Age:", width=22, anchor=tk.W).pack(side=tk.LEFT, padx=(0, 8))
        self.age_var = tk.StringVar()
        self._liv_entry(f, textvariable=self.age_var, width=10).pack(side=tk.LEFT)

        f = ttk.Frame(input_frame)
        f.pack(fill=tk.X, pady=2)
        ttk.Label(f, text="Height (in):", width=22, anchor=tk.W).pack(side=tk.LEFT, padx=(0, 8))
        self.height_var = tk.StringVar()
        self._liv_entry(f, textvariable=self.height_var, width=10).pack(side=tk.LEFT)

        f = ttk.Frame(input_frame)
        f.pack(fill=tk.X, pady=2)
        ttk.Label(f, text="Weight (lbs):", width=22, anchor=tk.W).pack(side=tk.LEFT, padx=(0, 8))
        self.weight_var = tk.StringVar()
        self._liv_entry(f, textvariable=self.weight_var, width=10).pack(side=tk.LEFT)

        f = ttk.Frame(input_frame)
        f.pack(fill=tk.X, pady=2)
        ttk.Label(f, text="BMI:", width=22, anchor=tk.W).pack(side=tk.LEFT, padx=(0, 8))
        self.bmi_label = tk.Label(f, text="—", width=10, bg=LIV["panel"], fg=LIV["primary"], font=("Helvetica", 10))
        self.bmi_label.pack(side=tk.LEFT)
        self.weight_var.trace_add("write", self._update_bmi)
        self.height_var.trace_add("write", self._update_bmi)

        f = ttk.Frame(input_frame)
        f.pack(fill=tk.X, pady=2)
        ttk.Label(f, text="Tobacco:", width=22, anchor=tk.W).pack(side=tk.LEFT, padx=(0, 8))
        self.tobacco_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(f, text="Yes", variable=self.tobacco_var).pack(side=tk.LEFT)

        f = ttk.Frame(input_frame)
        f.pack(fill=tk.X, pady=2)
        ttk.Label(f, text="Diabetes:", width=22, anchor=tk.W).pack(side=tk.LEFT, padx=(0, 8))
        self.diabetes_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(f, text="Yes", variable=self.diabetes_var).pack(side=tk.LEFT)

        f = ttk.Frame(input_frame)
        f.pack(fill=tk.X, pady=2)
        ttk.Label(f, text="Hypertension:", width=22, anchor=tk.W).pack(side=tk.LEFT, padx=(0, 8))
        self.htn_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(f, text="Yes", variable=self.htn_var).pack(side=tk.LEFT)

        f = ttk.Frame(input_frame)
        f.pack(fill=tk.X, pady=2)
        ttk.Label(f, text="Cancer history (years ago):", width=22, anchor=tk.W).pack(side=tk.LEFT, padx=(0, 8))
        self.cancer_var = tk.StringVar()
        self._liv_entry(f, textvariable=self.cancer_var, width=10).pack(side=tk.LEFT)
        ttk.Label(f, text="(blank = none)").pack(side=tk.LEFT, padx=(8, 0))

        f = ttk.Frame(input_frame)
        f.pack(fill=tk.X, pady=2)
        ttk.Label(f, text="DUI (years ago):", width=22, anchor=tk.W).pack(side=tk.LEFT, padx=(0, 8))
        self.dui_var = tk.StringVar()
        self._liv_entry(f, textvariable=self.dui_var, width=10).pack(side=tk.LEFT)
        ttk.Label(f, text="(blank = none)").pack(side=tk.LEFT, padx=(8, 0))

        # Knockouts & declinable conditions (scrollable)
        cond_outer, cond_inner_holder = self._liv_frame(main)
        cond_outer.pack(fill=tk.BOTH, expand=False, pady=(8, 12))
        ttk.Label(cond_inner_holder, text="Knockouts & conditions", font=("Helvetica", 11, "bold")).pack(anchor=tk.W, pady=(0, 4))
        canvas = tk.Canvas(cond_inner_holder, highlightthickness=0, bg=LIV["panel"])
        scrollbar = ttk.Scrollbar(cond_inner_holder, orient=tk.VERTICAL, command=canvas.yview)
        cond_inner = ttk.Frame(canvas)
        cond_inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=cond_inner, anchor=tk.NW)
        canvas.configure(yscrollcommand=scrollbar.set)
        self.condition_vars: dict[str, tk.BooleanVar] = {}
        conditions = get_conditions()
        knockouts = [c for c in conditions if c["category"] == "knockout"]
        declinable = [c for c in conditions if c["category"] == "declinable"]
        ncol = 2
        for i, c in enumerate(knockouts):
            var = tk.BooleanVar(value=False)
            self.condition_vars[c["code"]] = var
            ttk.Checkbutton(cond_inner, text=c["name"], variable=var).grid(
                row=i // ncol, column=i % ncol, sticky=tk.W, padx=(0, 14), pady=1
            )
        offset = (len(knockouts) + ncol - 1) // ncol
        for i, c in enumerate(declinable):
            var = tk.BooleanVar(value=False)
            self.condition_vars[c["code"]] = var
            ttk.Checkbutton(cond_inner, text=c["name"], variable=var).grid(
                row=offset + i // ncol, column=i % ncol, sticky=tk.W, padx=(0, 14), pady=1
            )
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind("<MouseWheel>", _on_mousewheel)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.configure(height=120)

        ttk.Button(main, text="Assess", command=self._run_assessment).pack(pady=12)

        # Results
        results_outer, results_inner = self._liv_frame(main)
        results_outer.pack(fill=tk.BOTH, expand=True, pady=(0, 12))
        ttk.Label(results_inner, text="Results", font=("Helvetica", 11, "bold")).pack(anchor=tk.W, pady=(0, 8))
        results_frame = results_inner

        columns = ("carrier", "rating", "notes")
        self.tree = ttk.Treeview(results_frame, columns=columns, show="headings", height=12)
        self.tree.heading("carrier", text="Carrier")
        self.tree.heading("rating", text="Likely Rating")
        self.tree.heading("notes", text="Notes")
        self.tree.column("carrier", width=200)
        self.tree.column("rating", width=100)
        self.tree.column("notes", width=320)
        self.tree.tag_configure("success", foreground=LIV["success"])
        self.tree.tag_configure("warn", foreground=LIV["warn"])
        self.tree.tag_configure("decline", foreground=LIV["decline"])
        self.tree.tag_configure("neutral", foreground=LIV["neutral"])
        self.tree.pack(fill=tk.BOTH, expand=True)

        scroll = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scroll.set)

        ttk.Label(main, text="Tip: Edit underwriting.db or add carriers in the database to use your real guidelines.", font=("Helvetica", 9), foreground=LIV["subtext"]).pack(anchor=tk.W, pady=(4, 0))

    def _update_bmi(self, *args):
        try:
            h = float(self.height_var.get() or 0)
            w = float(self.weight_var.get() or 0)
            if h > 0 and w > 0:
                bmi = round(w / (h * h) * 703, 1)
                self.bmi_label.config(text=str(bmi))
            else:
                self.bmi_label.config(text="—")
        except ValueError:
            self.bmi_label.config(text="—")

    def _get_client(self) -> dict:
        def safe_int(s, default=None):
            if not s or not s.strip():
                return default
            try:
                return int(s.strip())
            except ValueError:
                return default

        def safe_float(s, default=None):
            if not s or not s.strip():
                return default
            try:
                return float(s.strip())
            except ValueError:
                return default

        bmi = None
        h = safe_float(self.height_var.get())
        w = safe_float(self.weight_var.get())
        if h and w and h > 0 and w > 0:
            bmi = round(w / (h * h) * 703, 1)

        cancer = safe_int(self.cancer_var.get())
        dui = safe_int(self.dui_var.get())
        if dui is None:
            dui = 999

        conditions = {code for code, var in self.condition_vars.items() if var.get()}
        return {
            "age": safe_int(self.age_var.get()),
            "height": h,
            "weight": w,
            "bmi": bmi,
            "tobacco": self.tobacco_var.get(),
            "diabetes": self.diabetes_var.get(),
            "hypertension": self.htn_var.get(),
            "cancer_history_years": cancer if cancer is not None else 999,
            "dui_years_ago": dui,
            "conditions": conditions,
        }

    def _run_assessment(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

        client = self._get_client()
        product_type = self.product_var.get() or "IUL"
        carriers = get_carriers(product_type=product_type)

        if not carriers:
            messagebox.showinfo("No Carriers", f"No {product_type} carriers in database. Add carrier guidelines first.")
            return

        results = assess(client, carriers)
        for r in results:
            rating = r["rating"] if r["rating"] is not None else "Declined"
            if r["declined"]:
                tag = "decline"
            elif rating in ("Standard", "Elite", "Preferred Plus", "Preferred"):
                tag = "success"
            elif rating == "Graded":
                tag = "neutral"
            else:
                tag = "warn"
            self.tree.insert("", tk.END, values=(r["carrier"], rating, r["notes"]), tags=(tag,))

        if not results:
            messagebox.showinfo("Assessment", "No carriers matched. Client may be outside guidelines for all loaded carriers.")


def main():
    root = tk.Tk()
    app = UnderwritingApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
