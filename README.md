# Personal Loan Eligibility Model — India

A rule-based eligibility engine that tells an applicant **which of the top 20 Indian lenders will approve their personal loan**, for how much, at what interest rate, and why others rejected them.

---

## How to Run

```bash
python main.py
```

Answer 9 questions about your profile. The model instantly checks all 20 lenders and shows:
- Which lenders approve you
- Maximum loan amount from each
- Expected interest rate and monthly EMI
- The single best option and why
- Which lenders rejected you and the exact reason

To run all 10 pre-built test profiles at once:

```bash
python tests/test_profiles.py
```

---

## Repository Structure

```
Birbal/
├── data/
│   ├── input_variables.csv   — 13 input variables with type, unit, source
│   ├── lender_rules.csv      — Rules for 20 lenders with source links and dates
│   └── hidden_rules.csv      — 33 unlisted rules discovered from calculators and FAQs
├── model/
│   └── eligibility_engine.py — Core rule-based decision engine
├── tests/
│   └── test_profiles.py      — 10 edge-case test profiles with outputs
└── main.py                   — Interactive terminal interface
```

---

## How We Chose the Top 20 Lenders

We selected lenders based on three criteria:

1. **Market share** — RBI data and loan aggregator rankings (BankBazaar, PaisaBazaar) for personal loan disbursals in India
2. **Coverage diversity** — Mix of public sector banks, private banks, NBFCs, and fintech lenders to reflect the full market
3. **Public availability of rules** — Lenders with at least partial eligibility information available publicly

**Final list by category:**

| Category | Lenders |
|---|---|
| Public Sector Banks | SBI, Punjab National Bank, Bank of Baroda, Canara Bank, Union Bank of India |
| Private Banks | HDFC Bank, ICICI Bank, Axis Bank, Kotak Mahindra Bank, IndusInd Bank, Yes Bank, IDFC First Bank, Federal Bank |
| NBFCs | Bajaj Finserv, Tata Capital, Fullerton India, Muthoot Finance, Manappuram Finance |
| Fintech Lenders | Home Credit India, KreditBee |

---

## Approach and Methodology

### Step 1 — Rule Collection
For each lender we collected rules from:
- Official product pages and eligibility pages
- Eligibility calculators (tested with boundary inputs to find hidden thresholds)
- FAQs and product terms
- Loan comparison aggregators (BankBazaar, PaisaBazaar, WishFin, CreditMantri)

### Step 2 — Input Variables
Defined 13 input variables covering all dimensions a lender evaluates:
age, monthly income, employer type, employment tenure, city tier, CIBIL score, existing EMIs, loan amount, and tenure.

### Step 3 — Rule Table
Built one row per lender with 18 columns covering every rule dimension. Each rule has a source URL, collection date, and a confirmed/estimated flag.

### Step 4 — Model
Built a rule-based engine in Python. For each lender the engine runs 9 checks in sequence:
age → income → CIBIL → employment tenure → employer type → loan amount → tenure → city tier → FOIR → salary multiple

If any check fails, the lender rejects the applicant with a specific reason. If all checks pass, the engine calculates the offer (max loan, likely rate, EMI).

The best option is selected as the lender with the lowest likely interest rate among all approving lenders.

---

## Assumptions Made

1. **Interest rate estimation** — Banks publish a range (e.g. 10.5%–21%). We estimate the likely rate based on CIBIL score: CIBIL 750+ gets minimum rate, CIBIL 700–749 gets 30% into the range, below 700 gets 60% into the range. This is an approximation — actual rate also depends on employer category and income level.

2. **Salary multiple = 20x for most lenders** — Most lenders do not publicly state a salary multiple. We used 20x as the standard industry default, with confirmed values (27x for HDFC, 24x for SBI and PNB) where published.

3. **FOIR calculation uses existing EMI only** — We do not include credit card minimum payments in FOIR since that data is not collected. This slightly understates the true FOIR for credit card holders.

4. **City tier classification** — Based on population: Tier 1 (10 lakh+), Tier 2 (1–10 lakh), Tier 3 (below 1 lakh). Some lenders use their own city classifications which may differ slightly.

5. **Employer type is self-reported** — The model cannot verify whether an employer is truly MNC or PSU. In practice, banks verify this through salary slips and appointment letters.

---

## How We Found Unlisted Rules

Banks hide many rules that only surface when you test their calculators with boundary inputs. Our method:

**CIBIL threshold discovery:**
Entered scores from 800 down to 550 in steps of 10. Recorded the exact score where the calculator switches from "eligible" to "not eligible."

**Income threshold discovery:**
Entered income from high to low until the calculator showed rejection. Found that some banks (Kotak, Axis) have different thresholds for existing vs new customers.

**Employer type discovery:**
Systematically tested all employer types in calculators. Found that IndusInd and Yes Bank reject Self-Employed through their online calculators even though this is not stated on their product pages.

**FOIR and salary multiple:**
Kept all inputs constant and increased the loan amount until rejection. Divided the rejection threshold by monthly income to derive the implied salary multiple.

**Scheme variations:**
SBI has two underpublicised schemes — Xpress Credit (salary account holders) and Xpress Elite (Select Corporate list) — each with different limits. This was found in product FAQs, not the main product page.

All discovered hidden rules are documented with source and method in `data/hidden_rules.csv`.

---

## Key Insights

### 1. CIBIL score is the single biggest filter
Across all 10 test profiles, a CIBIL score below 650 eliminated 18 out of 20 lenders instantly. Only Home Credit and KreditBee accept applicants with no credit history at all — but at rates of 30%–56% per year.

### 2. Employment tenure fails more applicants than income
New job applicants (under 6 months) are rejected by 19 out of 20 lenders. Even applicants with good income and CIBIL are rejected by all PSU banks (SBI, PNB, Canara, Union Bank) if they have less than 24 months at their current employer.

### 3. Public sector banks are stricter on tenure, private banks on income
PSU banks (SBI, PNB, Canara, Union Bank) require 24 months minimum employment — the highest in the market. Private banks (HDFC, ICICI, Axis) require only 12 months. Fintech lenders (KreditBee) accept 3 months.

### 4. FOIR is the hidden rejector for middle-income applicants
An applicant earning Rs.50,000 with existing EMIs of Rs.30,000 has a FOIR of 60%. This eliminates most banks whose limit is 50%. Only Tata Capital (75% FOIR limit), Fullerton (65%), and Manappuram (60%) approve such applicants — at much higher rates.

### 5. Self-employed applicants are poorly served
Only 5 out of 20 lenders accept self-employed applicants (Bajaj Finserv, Tata Capital, Fullerton, Muthoot, Manappuram). All 5 charge significantly higher rates than they offer to salaried applicants at the same income level.

### 6. Interest rate spread is extreme — 10.4% to 56%
Punjab National Bank offers the lowest rate (10.4%) for strong profiles. Home Credit India charges up to 56% for weak profiles. The difference in EMI on a Rs.3 lakh loan over 3 years is Rs.4,500 per month — a 70% difference.

### 7. Tier-3 city applicants lose access to 6 lenders
IndusInd Bank, Yes Bank, Tata Capital, IDFC First Bank, Muthoot Finance, and Manappuram Finance either do not serve Tier-3 cities or have very limited presence. This reduces options significantly for small-town applicants.

---

## Model Limitations

1. **No real-time data** — Lender rules change frequently. All rules were collected on 2026-10-11. Always verify current rules before applying.

2. **Employer category not modelled** — HDFC, Kotak, and Tata Capital have internal employer category lists (A/B/C) that affect both eligibility and rates. The model uses employer type (MNC/PSU/Private) but cannot replicate the internal tiering without access to those lists.

3. **Bank relationship not modelled** — Existing customers of HDFC, ICICI, Axis, and Kotak get lower income thresholds and better rates. The model applies the standard (non-customer) threshold for all applicants.

4. **Interest rate is an estimate** — The actual rate offered depends on income, employer, city, and existing relationship — not just CIBIL. Our CIBIL-based estimation is a reasonable approximation but will differ from actual offers.

5. **Self-employed income verification not modelled** — ICICI requires 3 years business stability + Rs.15 lakh turnover + Rs.1 lakh PAT for self-employed. The model only checks employer type without these additional conditions.

6. **No soft rejection modelling** — Some banks do a soft rejection based on too many recent loan inquiries in the bureau report. This is not modelled as it requires bureau data beyond what we collect.

---

## What We Would Add Next

- Live rule updates by scraping lender websites on a schedule
- Employer category lookup using a company database
- Bank relationship flag as an input variable
- Self-employed specific income verification rules
- Bureau inquiry count as an input to model soft rejections
- Web interface for easier access
