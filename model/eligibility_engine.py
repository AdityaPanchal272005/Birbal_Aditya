import pandas as pd
import os

DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'lender_rules.csv')


def load_lender_rules():
    return pd.read_csv(DATA_PATH)


def calculate_foir(existing_emi_monthly, monthly_net_income):
    """Fixed Obligation to Income Ratio in percent."""
    if monthly_net_income <= 0:
        return 100.0
    return (existing_emi_monthly / monthly_net_income) * 100


def estimate_emi(loan_amount, annual_rate_pct, tenure_months):
    """Standard reducing balance EMI formula."""
    r = (annual_rate_pct / 100) / 12
    if r == 0:
        return loan_amount / tenure_months
    emi = loan_amount * r * (1 + r) ** tenure_months / ((1 + r) ** tenure_months - 1)
    return round(emi, 2)


def check_lender(applicant, lender_row):
    """
    Check a single applicant profile against one lender's rules.
    Returns (eligible: bool, reasons: list, details: dict).
    """
    reasons = []

    # Age check
    if applicant['age'] < lender_row['min_age']:
        reasons.append(f"Age {applicant['age']} below minimum {lender_row['min_age']}")
    if applicant['age'] > lender_row['max_age']:
        reasons.append(f"Age {applicant['age']} above maximum {lender_row['max_age']}")

    # Income check
    if applicant['monthly_net_income'] < lender_row['min_monthly_income_inr']:
        reasons.append(
            f"Monthly income ₹{applicant['monthly_net_income']:,} below minimum ₹{lender_row['min_monthly_income_inr']:,}"
        )

    # CIBIL check — 0 means no credit history
    required_cibil = lender_row['min_cibil_score']
    applicant_cibil = applicant['cibil_score']
    if required_cibil > 0 and applicant_cibil < required_cibil:
        if applicant_cibil == 0:
            reasons.append(f"No credit history; lender requires CIBIL ≥ {required_cibil}")
        else:
            reasons.append(f"CIBIL score {applicant_cibil} below minimum {required_cibil}")

    # Employment tenure check
    if applicant['employment_tenure_months'] < lender_row['min_employment_tenure_months']:
        reasons.append(
            f"Employment tenure {applicant['employment_tenure_months']} months "
            f"below minimum {lender_row['min_employment_tenure_months']} months"
        )

    # Employer type check
    accepted = [e.strip() for e in lender_row['accepted_employer_types'].split(',')]
    if applicant['employer_type'] not in accepted:
        reasons.append(
            f"Employer type '{applicant['employer_type']}' not accepted; "
            f"allowed: {', '.join(accepted)}"
        )

    # Loan amount check
    if applicant['loan_amount_requested'] < lender_row['min_loan_amount_inr']:
        reasons.append(
            f"Requested amount ₹{applicant['loan_amount_requested']:,} below minimum "
            f"₹{lender_row['min_loan_amount_inr']:,}"
        )
    if applicant['loan_amount_requested'] > lender_row['max_loan_amount_inr']:
        reasons.append(
            f"Requested amount ₹{applicant['loan_amount_requested']:,} exceeds maximum "
            f"₹{lender_row['max_loan_amount_inr']:,}"
        )

    # Salary multiple check — max loan cannot exceed X times monthly income
    salary_multiple_limit = applicant['monthly_net_income'] * lender_row['max_salary_multiple']
    if applicant['loan_amount_requested'] > salary_multiple_limit:
        reasons.append(
            f"Requested amount ₹{applicant['loan_amount_requested']:,} exceeds "
            f"{int(lender_row['max_salary_multiple'])}x salary limit of ₹{salary_multiple_limit:,.0f}"
        )

    # Tenure check
    if applicant['loan_tenure_months'] < lender_row['min_tenure_months']:
        reasons.append(
            f"Requested tenure {applicant['loan_tenure_months']} months below minimum "
            f"{lender_row['min_tenure_months']} months"
        )
    if applicant['loan_tenure_months'] > lender_row['max_tenure_months']:
        reasons.append(
            f"Requested tenure {applicant['loan_tenure_months']} months exceeds maximum "
            f"{lender_row['max_tenure_months']} months"
        )

    # City tier check
    allowed_tiers = [t.strip() for t in lender_row['city_tier_allowed'].split(',')]
    if applicant['city_tier'] not in allowed_tiers:
        reasons.append(
            f"City tier '{applicant['city_tier']}' not served; allowed: {', '.join(allowed_tiers)}"
        )

    # FOIR check
    foir = calculate_foir(applicant['existing_emi_monthly'], applicant['monthly_net_income'])
    if foir > lender_row['max_foir_pct']:
        reasons.append(
            f"FOIR {foir:.1f}% exceeds lender limit of {lender_row['max_foir_pct']}%"
        )

    if reasons:
        return False, reasons, {}

    # Eligible — compute offer details
    salary_cap = applicant['monthly_net_income'] * lender_row['max_salary_multiple']
    max_loan = min(applicant['loan_amount_requested'], lender_row['max_loan_amount_inr'], salary_cap)
    rate_min = lender_row['interest_rate_min_pct']
    rate_max = lender_row['interest_rate_max_pct']
    tenure = applicant['loan_tenure_months']

    # Estimate likely rate based on CIBIL score
    cibil = applicant['cibil_score']
    if cibil >= 750:
        likely_rate = rate_min
    elif cibil >= 700:
        likely_rate = rate_min + (rate_max - rate_min) * 0.3
    elif cibil == 0:
        likely_rate = rate_max
    else:
        likely_rate = rate_min + (rate_max - rate_min) * 0.6

    emi = estimate_emi(max_loan, likely_rate, tenure)

    details = {
        'max_loan_amount': max_loan,
        'interest_rate_range': f"{rate_min}%-{rate_max}%",
        'likely_rate_pct': round(likely_rate, 2),
        'tenure_months': tenure,
        'estimated_emi': emi,
        'foir_after_new_loan': round(
            (applicant['existing_emi_monthly'] + emi) / applicant['monthly_net_income'] * 100, 1
        ),
    }
    return True, [], details


def check_eligibility(applicant: dict) -> dict:
    """
    Main function. Takes an applicant profile dict and returns eligibility result.

    Required keys in applicant:
        age, monthly_net_income, employer_type, employment_tenure_months,
        city_tier, cibil_score, existing_emi_monthly, loan_amount_requested,
        loan_tenure_months
    """
    rules_df = load_lender_rules()

    approving_lenders = []
    rejected_lenders = []

    for _, row in rules_df.iterrows():
        eligible, reasons, details = check_lender(applicant, row)
        if eligible:
            approving_lenders.append({
                'lender': row['lender'],
                **details,
            })
        else:
            rejected_lenders.append({
                'lender': row['lender'],
                'rejection_reasons': reasons,
            })

    # Pick best option: lowest likely rate among approving lenders
    best_option = None
    if approving_lenders:
        best_option = min(approving_lenders, key=lambda x: x['likely_rate_pct'])

    return {
        'eligible': len(approving_lenders) > 0,
        'approving_lenders_count': len(approving_lenders),
        'approving_lenders': approving_lenders,
        'rejected_lenders': rejected_lenders,
        'best_option': best_option,
    }
