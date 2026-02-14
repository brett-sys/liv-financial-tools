# Underwriting Risk Assessment Tool

Run the app:
```bash
python3 underwriting_tool.py
```

## Product Types

Use the **Product type** dropdown to filter carriers:
- **IUL** – Indexed Universal Life (default)
- **Term** – Term life (10–40 year)
- **Final Expense** – Burial/simplified issue ($5K–$35K)

## Pre-loaded Carriers

### Ethos (Ameritas IUL)
From IUL Underwriting One-Pager. BMI 18–49. Diabetes OK if age 35+, no complications, A1C ≤9.5, BMI ≤41.49. DUI 5yr. Cancer 10yr. BP limits by age.

### Americo (Instant Decision IUL)
From IULAgentGuide. Ages 18-65. $50K-$450K non-medical. Build chart max ~42 BMI. No substandard. Non-nicotine 24mo.

### Mutual of Omaha (IUL Express)
From Underwriting IUL MOO guide. Simplified issue. Ages 18-75. Standard build ~42 BMI; Table 2 (multiple impairments) ~38 BMI. Diabetes decline. HTN treatment allowed. Tobacco 12mo. DUI 5yr. Prior Table 4+ or decline = ineligible.

### Transamerica (FFIUL)
From height/weight charts (Female & Male, Ages 18-70). FFIUL & TFLIC FFIUL. Preferred Elite through Standard. Charts differ by age (71+) and gender—tool uses approximate BMI. Trendsetter LB bands 3 & 4.

### National Life (Permanent)
From National Life General Underwriting Guide. SummitLife/PeakLife/FlexLife IUL.
- **Diabetes:** Decline for preferred classes
- **Hypertension:** OK if controlled (one med)
- **DUI:** 5 years for table, 10 years for standard
- **Cancer:** 3–5 years – contact underwriter

### Term carriers (from FFL-LIV underwriting guides: 2023 Term Grid, Ethos Knockout Guide, InstaBrain, Ladder, Family Freedom)
- **Ethos Term** – TLE/IULE. Prime ($2M), Spectrum ($500K), Select ($150K). DUI 5yr. Many conditions→Select or FE.
- **InstaBrain Term** – Fidelity Life. P+ 18–28 BMI, P 29–30, Std 31–32, StdEx 33–37. Height/weight build chart. Ages 18–60. Diabetes/insulin/cancer decline.
- **Ladder (Term)** – Prosperity LadderLife. P+ 18–28, P 29–30, Std+ 31–32, Std 33–37. DUI 5yr. Type 2 diabetes OK if controlled.
- **Family Freedom Term** – Transamerica. 18–75, $50K–$500K simplified. 10–30yr level term. Living benefit riders.
- **TruStage Term** – Home Mortgage Series / Term Made Simple. Strict UW. DUI 10yr.

### Final Expense carriers (from FFL-LIV UW guides: Final Expense Grid, Eagle Select, RAPIDecision GI, Royal Neighbors)
- **Accendo (Final Expense)** – Aetna/CVS. $2K–$50K. Ages 40–89. Level & Modified. Many conditions allowed or GI.
- **Americo Eagle Select** – Ages 40–85. Up to $40K. 3 tiers. Quit Smoking Advantage. Instant decision.
- **Fidelity Life RAPIDecision GI** – Guaranteed Issue. Ages 50–85. $5K–$25K. No underwriting. Graded benefit yrs 1–3.
- **Royal Neighbors Ensured Legacy** – Preferred/Standard/GDB/GI tiers. Diabetes no insulin OK.
- **Living Promise (Final Expense)** – From FE Grid. Cancer >4yr allowed. DUI 2yr.

### Build Table Carrier
Generic carrier using the Elite Preferred → Standard 2 build table (same as National Life permanent):

| BMI Range | Rate Class |
|-----------|------------|
| &lt; 27.1 | Elite Preferred |
| 27.1 – 29.9 | Select Standard |
| 29.9 – 32.7 | Express Standard 1 |
| 32.7 – 37.5 | Express |
| 37.5 – 42.5 | Standard 2 |
| 42.5 – 46.5 | Table 8 |
| &gt; 46.5 | Decline |

Rename "Build Table Carrier" in the database to your actual carrier name if needed.

## How It Works

1. Enter client factors: age, height, weight, tobacco, conditions, etc.
2. BMI is auto-calculated from height/weight.
3. Click **Assess** to see which carriers likely approve and at what rating.
4. Results are sorted by best rating first.

## Adding Your Real Carrier Data

The app uses a SQLite database: `underwriting.db` (created in the same folder on first run).

### Option 1: Edit with a DB browser

Use [DB Browser for SQLite](https://sqlitebrowser.org/) or similar:

1. Open `underwriting.db`
2. Edit the `carriers` table or add new rows
3. Column reference below

### Option 2: Run SQL directly

```bash
sqlite3 underwriting.db
```

```sql
-- Example: Add a real carrier
INSERT INTO carriers (
  name, product_type,
  bmi_max_standard, bmi_max_table2, bmi_max_table4,
  min_age, max_age,
  tobacco_standard, tobacco_table2, tobacco_decline,
  diabetes_ok, hypertension_ok, cancer_history_years,
  dui_years_standard, dui_years_table, notes
) VALUES (
  'Nationwide', 'IUL',
  35.0, 38.0, 42.0,   -- BMI limits
  18, 85,              -- age range
  0, 1, 0,             -- tobacco: 0=no standard, 1=table ok, 0=no decline
  2, 2, 10, 10, 5,     -- diabetes ok, htn ok, cancer 10yr, dui 10/5
  'Check current UW guide'
);
```

### Carrier Columns

| Column | Meaning |
|--------|---------|
| `bmi_max_standard` | Max BMI for Standard (e.g. 35) |
| `bmi_max_table2` | Max BMI for Table 2 |
| `bmi_max_table4` | Max BMI for Table 4 |
| `bmi_max_table6` | Max BMI for Table 6 (optional) |
| `bmi_max_table8` | Max BMI for Table 8 (optional; above = decline) |
| `min_age`, `max_age` | Age limits |
| `tobacco_standard` | 1 = tobacco can get Standard |
| `tobacco_table2` | 1 = tobacco gets Table rating |
| `tobacco_decline` | 1 = tobacco decline |
| `diabetes_ok` | 0=decline, 1=table, 2=standard |
| `hypertension_ok` | Same |
| `cancer_history_years` | Min years since cancer (e.g. 10) |
| `dui_years_standard` | Min years since DUI for Standard |
| `dui_years_table` | Min years for Table (below = decline) |

## Knockouts & Declinable Conditions

The tool includes a **Knockouts & conditions** section based on common impairments that may result in adjusted benefit or decline.

### Knockouts (typically decline at most carriers)
- HIV/AIDS
- Organ / bone marrow transplant
- ALS / MS / Parkinson's
- Current dialysis / renal failure
- Drug/substance abuse (current)
- Prior life insurance decline
- Metastatic or recurrent cancer
- Mental incapacity
- Paralysis
- Sickle cell anemia

### Declinable conditions (table at full UW carriers, decline at simplified/instant)
- Abnormal/irregular heart rhythm
- Alcohol or drug treatment history
- Amputation caused by disease
- Asthma (chronic or severe)
- Bipolar / schizophrenia / major depression
- Cardiomyopathy
- Cerebral palsy
- Chronic kidney disease
- Congestive heart failure (CHF)
- Crohn's disease / ulcerative colitis
- Coronary disease / heart attack / heart surgery
- COPD / chronic bronchitis / emphysema / cystic fibrosis
- Cancer
- Defibrillator
- Diabetes with complications
- Heart disease or surgery
- Hepatitis B or C
- Hodgkin's disease
- Liver disease / cirrhosis
- Leukemia
- Lymphoma
- Melanoma
- Muscular dystrophy / neurological disorders
- Pacemaker
- Pancreatitis (chronic or alcohol-related)
- Peripheral vascular disease (PVD/PAD)
- Renal insufficiency / kidney disease
- Rheumatoid arthritis (moderate/severe)
- Scleroderma
- Stroke or TIA
- Seizure disorder
- Sleep apnea (untreated/severe)

Carrier-specific rules are stored in `carrier_conditions`. Americo and Mutual of Omaha (instant/simplified issue) decline these conditions; National Life, Transamerica, Ethos (full UW) apply table rating.

### Adding more conditions

```sql
INSERT INTO conditions (code, name, category) VALUES ('my_condition', 'Display Name', 'declinable');
INSERT INTO carrier_conditions (carrier_id, condition_code, action) VALUES (5, 'my_condition', 'decline');
```

## Extending the Tool

- Add more conditions (e.g. aneurysm, lupus) to `conditions` and `carrier_conditions`
- Add more carriers from your carrier UW guides
- Export the `carriers` table to CSV for backup
- Update limits when carriers change their guidelines
