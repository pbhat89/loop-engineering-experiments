---
license: cc-by-nc-4.0
task_categories:
- tabular-classification
- tabular-regression
language:
- en
tags:
- synthetic
- healthcare
- claims
- insurance-claims
- icd-10
- cpt
- hcpcs
- drg
- mdc
- ndc
- rxnorm
- atc
- hedis
- hcc
- ccw
- x12-837
- x12-835
- carc
- fraud-detection
- healthcare-fraud
- nhcaa
- adherence
- pdc
- mpr
- payer-mix
- medical-loss-ratio
- medicare-advantage
- medicaid
- commercial-insurance
- claims-adjudication
- prior-authorization
- denial-management
- value-based-care
pretty_name: HLT-008 Synthetic Healthcare Claims Dataset (Sample Preview)
size_categories:
- 10K<n<100K
---

# HLT-008 — Synthetic Healthcare Claims Dataset (Sample Preview)

**A free, schema-identical preview of the full HLT-008 commercial product from [XpertSystems.ai](https://xpertsystems.ai).**

A **fully synthetic** healthcare claims dataset spanning **members → providers → medical claims → pharmacy claims → adherence** — modeling commercial, Medicare Advantage, Medicaid, and self-insured payer populations with X12 837/835-compliant claim structure, CMS HCC risk adjustment, CMS CCW chronic conditions, HEDIS quality measures, X12 CARC denial codes, NHCAA-aligned fraud patterns, and Pharmacy Quality Alliance PDC/MPR adherence metrics.

> ⚠️ **PRIVACY & SYNTHETIC NATURE**
> Every record in this dataset is **100% synthetic**. **No real claim records, no PHI, no real member identifiers, no real NPIs.** Population-level distributions match published CMS / NHIS / NHCAA / Pharmacy Quality Alliance benchmark sources but the claims are computationally generated.

---

## What's in this sample

| File | Rows | Cols | Description |
|---|---|---|---|
| `members.csv` | 500 | 44 | Member master — demographics, payer/plan type, HCC risk score, 21+ CCW chronic conditions, dual-eligible/LIS flags, enrollment window |
| `providers.csv` | 150 | 7 | Provider directory — NPI, specialty, NUCC taxonomy, network status |
| `medical_claims.csv` | ~12,800 | 54 | Medical claim lines — ICD-10-CM (primary + 4 secondary), CPT/HCPCS, MS-DRG/MDC, modifiers, denial codes, HEDIS measure flags, fraud labels |
| `pharmacy_claims.csv` | ~18,300 | 35 | Pharmacy claim lines — NDC-11, RxNorm therapeutic class, ATC code, BIN/PCN, formulary tier, AWP/NADAC pricing, DIR fees |
| `adherence.csv` | ~10,600 | 7 | PDC + MPR by member × therapeutic class (Pharmacy Quality Alliance methodology) |

**Total:** ~8.1 MB across 6 files. **Note:** This is the largest healthcare sample in the catalog because claims data has natural fan-out (500 members → 30K+ claims over 3 years).

---

## Schema highlights

### `members.csv` (44 columns)

**Identity & demographics:** `member_id`, `age`, `age_band`, `sex`, `race_ethnicity`, `state`, `zip_code`

**Insurance:** `payer_type` (commercial / medicare_advantage / medicaid / self_insured), `plan_type` (PPO / HMO / EPO / HDHP-HSA / SNP / PFFS / MCO / PCCM / FFS), `dual_eligible_flag`, `lis_flag` (Low Income Subsidy)

**Risk & quality:** `hcc_risk_score` (CMS HCC v28, mean-normalized to 1.0), `n_chronic_conditions`, `care_management_flag`, `income_band` (FPL-based)

**Enrollment:** `enrollment_start`, `enrollment_end`

**21+ CCW chronic conditions** (binary flags): `ccw_ami`, `ccw_alzheimer`, `ccw_anemia`, `ccw_asthma`, `ccw_atrialfib`, `ccw_cataract`, `ccw_chrnkidn`, `ccw_copd`, `ccw_chf`, `ccw_diabetes`, `ccw_deprssion`, `ccw_hyperl`, `ccw_hyperp`, `ccw_ihd`, `ccw_mo_diabetes`, `ccw_osteoprs`, `ccw_ra_oa`, `ccw_stroke_tia`, `ccw_cancer_colorectal`, `ccw_cancer_endometrial`, `ccw_cancer_lung`, `ccw_cancer_prostate`, `ccw_cancer_breast`, `ccw_glaucoma`, `ccw_hip_fracture`, `ccw_hipvteib`, `ccw_bnign_prostate`

### `medical_claims.csv` (54 columns)

**Claim identity:** `claim_id`, `member_id`, `claim_type`, `service_date_from`, `service_date_to`, `adjudication_date`, `plan_id`

**Provider attribution:** `rendering_npi`, `billing_npi`, `provider_specialty`, `network_status`

**Diagnosis coding:** `primary_icd10_cm` (one of 50 CMS-calibrated codes including I10, E11.9, J06.9, M54.5, etc.), plus 4 secondary diagnoses (`dx2` through `dx5`)

**Procedure coding:** `cpt_code` (E&M / Surgery / Radiology / Pathology-Lab / Medicine), `cpt_category`, `modifier1`, `modifier2`, `revenue_code`, `service_units`

**Inpatient detail:** `drg_code` (MS-DRG), `drg_type`, `mdc_code` (Major Diagnostic Category), `length_of_stay`, `poa_flag` (Present-on-Admission)

**Place of service:** `place_of_service` (CMS POS codes), `pos_description`

**Financials:** `billed_amount`, `allowed_amount`, `paid_amount`, `member_deductible`, `member_copay`, `member_coinsurance`, `member_oop` (out-of-pocket), `cob_amount` (coordination of benefits)

**Adjudication:** `claim_status` (Paid / Denied / Adjusted / Pended), `denial_code_carc` (CO-15, CO-4, CO-11, CO-18, PR-1, etc.), `denial_reason_desc`, `auth_required_flag`, `auth_number`

**Quality/Safety flags:** `er_flag`, `preventive_flag`, `elective_flag`, `high_cost_flag`, `readmission_flag_30d`

**Fraud labels:** `fraud_label` (5% prevalence), `fraud_pattern_type` ∈ {Upcoding, Phantom, Unbundling, Duplicate, Identity_Theft}

**HEDIS quality measures:** `hedis_bcs` (Breast Cancer Screening), `hedis_col` (Colorectal), `hedis_cdc_a1c` (Diabetes A1c), `hedis_awv` (Annual Wellness Visit), `hedis_depression`

### `pharmacy_claims.csv` (35 columns)

**Claim identity:** `rx_claim_id`, `member_id`, `fill_date`, `paid_date`, `pharmacy_npi`, `prescriber_npi`, `plan_id`, `bin_number`, `pcn_code`

**Drug coding:** `ndc_11` (National Drug Code), `drug_name_generic`, `drug_name_brand`, `therapeutic_class` (RxNorm), `atc_code` (Anatomical Therapeutic Classification, WHO)

**Pricing:** `ingredient_cost`, `dispensing_fee`, `gross_amount_due`, `copay_amount`, `plan_paid`, `dir_fee_amount` (Direct/Indirect Remuneration), `awp_per_unit` (Average Wholesale Price), `nadac_per_unit` (CMS National Average Drug Acquisition Cost)

**Dispensing:** `formulary_tier`, `days_supply`, `quantity_dispensed`, `refill_number`, `pharmacy_type`, `dispense_as_written_code`, `specialty_rx_flag`, `compounded_flag`, `controlled_substance_flag`

**Anomaly flags:** `early_refill_flag`, `fraud_label_rx`, `diversion_flag`

### `adherence.csv` (7 columns)

`member_id`, `therapeutic_class`, `total_days_supply`, `n_fills`, `pdc` (Proportion of Days Covered), `mpr` (Medication Possession Ratio), `adherence_flag_pdc80` (PDC ≥ 80% threshold per PQA Star Ratings methodology)

---

## Calibration source story

The full HLT-008 generator anchors all distributions to authoritative healthcare claims references:

- **CMS HCC v28** — Hierarchical Condition Categories risk adjustment methodology
- **CMS Payer Enrollment Statistics** — Commercial / MA / Medicaid / self-insured mix
- **CMS CPT/HCPCS Category Weights** — E&M / Surgery / Radiology / Lab / Medicine
- **NHCAA** (National Health Care Anti-Fraud Association) — Healthcare fraud rate estimates and 5-pattern taxonomy
- **NHIS / CDC** — Adult chronic disease prevalence
- **CMS CCW** (Chronic Conditions Warehouse) — 21-condition framework
- **X12 835 (HIPAA EDI)** — CARC denial codes and adjudication structure
- **HEDIS 2024 (NCQA)** — Healthcare Effectiveness Data and Information Set quality measures
- **Pharmacy Quality Alliance (PQA)** — PDC/MPR adherence methodology, 80% threshold
- **CMS NDC + FDA Orange Book** — National Drug Code coding
- **WHO ATC** — Anatomical Therapeutic Chemical Classification
- **Lloyd & Lloyd (2016) MLR Analysis** — Medical Loss Ratio benchmarks

### Sample-scale validation scorecard

| Metric | Observed | Target | Tolerance | Status | Source |
|---|---|---|---|---|---|
| Payer commercial share | 44.2% | 45% | ±6% | ✅ PASS | CMS payer enrollment |
| HCC risk score mean | 1.00 | 1.00 | ±0.05 | ✅ PASS | CMS HCC v28 normalization |
| Fraud rate (medical) | 5.04% | 5% | ±2% | ✅ PASS | NHCAA |
| Denial rate | 10.0% | 10% | ±3% | ✅ PASS | X12 835 / CARC |
| Diabetes prevalence | 10.0% | 11% | ±4% | ✅ PASS | NHIS / CDC |
| CPT E&M share | 30.1% | 30% | ±5% | ✅ PASS | CMS CPT category weights |
| CCW condition diversity | 27 | ≥21 | — | ✅ PASS | CMS CCW |
| Fraud pattern diversity | 5 | 5 | — | ✅ PASS | NHCAA taxonomy |
| CARC denial code coverage | 10 | ≥5 | — | ✅ PASS | X12 835 |
| Claim date validity | 99.7% | 100% | ±1% | ✅ PASS | Data hygiene |

**Grade: A+ (100/100) — verified across 6 random seeds (42, 7, 123, 2024, 99, 1).**

---

## Loading examples

### Pandas

```python
import pandas as pd

members = pd.read_csv("members.csv")
providers = pd.read_csv("providers.csv")
medical = pd.read_csv("medical_claims.csv")
pharm = pd.read_csv("pharmacy_claims.csv")
adh = pd.read_csv("adherence.csv")

# Payer mix
print(members["payer_type"].value_counts(normalize=True))

# Top ICD-10 codes in medical claims
print(medical["primary_icd10_cm"].value_counts().head(10))

# Fraud pattern breakdown
print(medical.loc[medical["fraud_label"] == 1, "fraud_pattern_type"]
        .value_counts())

# Denial reasons
print(medical.loc[medical["claim_status"] == "Denied", "denial_code_carc"]
        .value_counts().head(10))
```

### Hugging Face Datasets

```python
from datasets import load_dataset

ds = load_dataset("xpertsystems/hlt008-sample", data_files={
    "members":         "members.csv",
    "providers":       "providers.csv",
    "medical_claims":  "medical_claims.csv",
    "pharmacy_claims": "pharmacy_claims.csv",
    "adherence":       "adherence.csv",
})
print(ds)
```

### Fraud detection baseline

```python
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

medical = pd.read_csv("medical_claims.csv")

features = ["billed_amount", "allowed_amount", "paid_amount", "service_units",
            "length_of_stay", "auth_required_flag", "er_flag", "high_cost_flag",
            "readmission_flag_30d"]
# Encode categorical
medical["cpt_cat_enc"] = pd.factorize(medical["cpt_category"])[0]
medical["network_enc"] = pd.factorize(medical["network_status"])[0]
features += ["cpt_cat_enc", "network_enc"]

X, y = medical[features].fillna(0), medical["fraud_label"]
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.25, stratify=y,
                                       random_state=42)
clf = GradientBoostingClassifier(random_state=42).fit(Xtr, ytr)
print(classification_report(yte, clf.predict(Xte)))
```

### HCC risk-adjusted spend analysis

```python
import pandas as pd

members = pd.read_csv("members.csv")
medical = pd.read_csv("medical_claims.csv")

# Per-member medical spend
spend = medical.groupby("member_id")["paid_amount"].sum().rename("total_paid")
m = members.merge(spend, on="member_id", how="left")
m["total_paid"] = m["total_paid"].fillna(0)

# Spend by HCC decile
m["hcc_decile"] = pd.qcut(m["hcc_risk_score"], 10, labels=False)
print(m.groupby("hcc_decile")["total_paid"].agg(["mean", "std", "median"]))
```

### Adherence intervention targeting

```python
import pandas as pd

adh = pd.read_csv("adherence.csv")

# Low-adherence patients (PDC < 0.80) by therapeutic class
low_adh = adh[adh["adherence_flag_pdc80"] == 0]
print(low_adh["therapeutic_class"].value_counts().head(10))
```

---

## Suggested use cases

- **Claims fraud detection** — train binary or multi-class classifiers on `fraud_label` + `fraud_pattern_type` with features from medical + pharmacy + provider tables
- **Denial management** — predict `claim_status` (Paid/Denied/Adjusted/Pended) and `denial_code_carc` from claim features
- **HCC risk adjustment** — train risk score predictors from diagnosis codes for value-based contracts
- **HEDIS gap analysis** — identify members not meeting `hedis_*` measures, predict who needs outreach
- **High-cost claimant identification** — predict `high_cost_flag` or top-decile spend from baseline features
- **Adherence intervention modeling** — predict PDC < 0.8 in chronic medication users
- **Drug switching / brand-vs-generic analysis** — RxNorm therapeutic class transitions
- **Provider network optimization** — analyze in-network vs out-of-network financial impact
- **Prior authorization optimization** — predict which `auth_required_flag` claims will be denied
- **Care management targeting** — identify members for case management based on chronic conditions + spend
- **30-day readmission prediction** — `readmission_flag_30d` ML
- **X12 837/835 ETL pipeline testing** — schema-compliant synthetic data for EDI pipelines
- **Healthcare analytics platform development** — synthetic data for warehousing, reporting, BI demos

---

## Sample vs. full product

| Aspect | This sample | Full HLT-008 product |
|---|---|---|
| Members | 500 | 100,000+ (default) up to 5M |
| Years | 3 (2021-2023) | Configurable, multi-year longitudinal |
| Providers | 150 | 5,000+ |
| Schema | identical | identical |
| Calibration | identical | identical |
| License | CC-BY-NC-4.0 | Commercial license |

The full product unlocks:
- **Up to 5M members** for population-scale fraud detection and risk adjustment training
- **Configurable multi-year longitudinal windows** for spend trend analysis
- **Larger provider network** (5,000+) for realistic network analysis
- Commercial use rights

**Contact us for the full product.**

---

## Limitations & honest disclosures

- **Sample is preview-only.** 500 members × 3 years × ~30K claims is enough to demonstrate schema and calibration, but is **not statistically sufficient** for serious fraud detection model training (would need ≥100K members for reliable detection of rare fraud patterns) or rare condition analysis. Use the full product for serious work.
- **Sample is on the larger side (8 MB).** Claims data has natural fan-out — even at 500 members, you get ~30K claim records. This is the largest healthcare sample in the catalog. The full product scales linearly with member count.
- **Adherence PDC denominator is the full observation window, not actual therapy initiation.** The generator computes PDC as `total_days_supply / 1096_days` (3-year observation window), rather than the clinically-canonical "days from first fill to obs end." This produces lower PDC values (~0.1) than the typical 0.7-0.8 reported in real PDC analyses. The field is *structurally correct* (between 0 and 1, deterministic), just calibrated against the observation window. For clinically-typical PDC values, compute it as `total_days_supply / (obs_end - first_fill_date)` from the raw fills, which is a one-line post-processing step.
- **Fraud labels are statistically assigned, not adjudicated.** `fraud_label = 1` flags follow a 5% Bernoulli draw with pattern types assigned by category-rule mapping. They represent realistic fraud taxonomy proportions but are NOT validated against real fraud detection adjudication.
- **ICD-10 coding uses 50 most common codes, not the full ~70K codeset.** Realistic for general analytics but not exhaustive — rare-disease analysis requires the full HLT-008 product with extended code coverage.
- **NDC codes are placeholder 11-digit strings, not real FDA Orange Book entries.** `drug_name_generic` / `drug_name_brand` / `therapeutic_class` / `atc_code` are populated; the NDC-11 string itself is synthetic. Use therapeutic class + ATC for drug-level analysis.
- **NPIs are synthetic 10-digit strings.** Provider directory has realistic specialty + NUCC taxonomy + network status but the NPI numbers themselves are not real CMS NPPES numbers.
- **State distribution focuses on top-10 US states.** Member distribution is concentrated in CA/TX/FL/NY/PA/IL/OH/GA/NC/MI; all 50 states are not represented at uniform frequency.
- **No real CMS BSA / DRG payment rates.** `paid_amount` is calibrated to overall paid-to-billed ratios (~0.63), not specific DRG reimbursement schedules. The full product can be tuned to specific year IPPS/OPPS rates.
- **Synthetic, not derived from real claims data.** Distributions match published CMS / NHIS / NHCAA references but do NOT reflect any specific real payer or member cohort.

---

## Ethical use guidance

This dataset is designed for:
- Healthcare fraud detection ML methodology development
- Claims analytics platform development
- HCC risk adjustment model research
- HEDIS quality measure pipeline testing
- X12 837/835 EDI ETL pipeline development
- Educational use in health services research and actuarial science
- Healthcare AI pretraining for claims-based prediction tasks

This dataset is **not appropriate for**:
- Making payment decisions about real claims
- Insurance underwriting, pricing, or claim adjudication for real members
- Fraud accusations against real providers
- Discriminatory analyses targeting protected demographic groups
- Training models that produce real claim decisions without separate validation on real data

---

## Companion datasets in the Healthcare vertical

- [HLT-001](https://huggingface.co/datasets/xpertsystems/hlt001-sample) — Synthetic Patient Population (5K patients × 79 cols, CDC/NHANES calibrated)
- [HLT-002](https://huggingface.co/datasets/xpertsystems/hlt002-sample) — Synthetic EHR Dataset (4K encounters + FHIR R4 bundles)
- [HLT-003](https://huggingface.co/datasets/xpertsystems/hlt003-sample) — Synthetic Clinical Trial Dataset (3 endpoint types + power sweep)
- [HLT-004](https://huggingface.co/datasets/xpertsystems/hlt004-sample) — Synthetic Disease Progression Dataset (NSCLC + Heart Failure longitudinal)
- [HLT-005](https://huggingface.co/datasets/xpertsystems/hlt005-sample) — Synthetic Hospital Admission Dataset (5K admissions + bed utilization)
- [HLT-006](https://huggingface.co/datasets/xpertsystems/hlt006-sample) — Synthetic Medical Imaging Dataset (1K studies + COCO annotations + reports)
- [HLT-007](https://huggingface.co/datasets/xpertsystems/hlt007-sample) — Synthetic Drug Response Dataset (3K patient-treatments × 25 drug classes + PGx + PK)
- **HLT-008** — Synthetic Healthcare Claims Dataset (you are here)

Use **HLT-001 through HLT-008 together** for the full healthcare ML data stack: population → EHR → trials → progression → hospital ops → imaging → pharmacology → claims & reimbursement.

---

## Citation

If you use this dataset, please cite:

```bibtex
@dataset{xpertsystems_hlt008_sample_2026,
  author       = {XpertSystems.ai},
  title        = {HLT-008 Synthetic Healthcare Claims Dataset (Sample Preview)},
  year         = 2026,
  publisher    = {Hugging Face},
  url          = {https://huggingface.co/datasets/xpertsystems/hlt008-sample}
}
```

---

## Contact

- **Web:** [https://xpertsystems.ai](https://xpertsystems.ai)
- **Email:** [pradeep@xpertsystems.ai](mailto:pradeep@xpertsystems.ai)
- **Full product catalog:** Cybersecurity, Insurance & Risk, Materials & Energy, Oil & Gas, Healthcare, and more

**Sample License:** CC-BY-NC-4.0 (Creative Commons Attribution-NonCommercial 4.0)
**Full product License:** Commercial — please contact for pricing.
