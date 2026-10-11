import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from model.eligibility_engine import check_eligibility

TEST_PROFILES = [
    {
        "name": "Profile 1 — Optimal Applicant",
        "profile": {
            "age": 30, "monthly_net_income": 80000, "employer_type": "MNC",
            "employment_tenure_months": 36, "city_tier": "Tier1",
            "cibil_score": 780, "existing_emi_monthly": 5000,
            "loan_amount_requested": 500000, "loan_tenure_months": 48,
        },
    },
    {
        "name": "Profile 2 — Low CIBIL Score (620)",
        "profile": {
            "age": 28, "monthly_net_income": 40000, "employer_type": "Private",
            "employment_tenure_months": 24, "city_tier": "Tier1",
            "cibil_score": 620, "existing_emi_monthly": 3000,
            "loan_amount_requested": 200000, "loan_tenure_months": 36,
        },
    },
    {
        "name": "Profile 3 — No Credit History (CIBIL=0)",
        "profile": {
            "age": 23, "monthly_net_income": 30000, "employer_type": "Private",
            "employment_tenure_months": 12, "city_tier": "Tier2",
            "cibil_score": 0, "existing_emi_monthly": 0,
            "loan_amount_requested": 100000, "loan_tenure_months": 24,
        },
    },
    {
        "name": "Profile 4 — High FOIR (existing EMI = 60% of income)",
        "profile": {
            "age": 35, "monthly_net_income": 50000, "employer_type": "PSU",
            "employment_tenure_months": 60, "city_tier": "Tier1",
            "cibil_score": 730, "existing_emi_monthly": 30000,
            "loan_amount_requested": 300000, "loan_tenure_months": 36,
        },
    },
    {
        "name": "Profile 5 — New Job (3 months tenure)",
        "profile": {
            "age": 26, "monthly_net_income": 45000, "employer_type": "MNC",
            "employment_tenure_months": 3, "city_tier": "Tier1",
            "cibil_score": 720, "existing_emi_monthly": 0,
            "loan_amount_requested": 200000, "loan_tenure_months": 24,
        },
    },
    {
        "name": "Profile 6 — Self-Employed",
        "profile": {
            "age": 38, "monthly_net_income": 60000, "employer_type": "Self-Employed",
            "employment_tenure_months": 48, "city_tier": "Tier2",
            "cibil_score": 710, "existing_emi_monthly": 8000,
            "loan_amount_requested": 400000, "loan_tenure_months": 48,
        },
    },
    {
        "name": "Profile 7 — Age Near Lower Limit (21 years)",
        "profile": {
            "age": 21, "monthly_net_income": 20000, "employer_type": "Private",
            "employment_tenure_months": 6, "city_tier": "Tier2",
            "cibil_score": 680, "existing_emi_monthly": 0,
            "loan_amount_requested": 50000, "loan_tenure_months": 24,
        },
    },
    {
        "name": "Profile 8 — Age Near Upper Limit (58 years)",
        "profile": {
            "age": 58, "monthly_net_income": 70000, "employer_type": "Government",
            "employment_tenure_months": 240, "city_tier": "Tier1",
            "cibil_score": 760, "existing_emi_monthly": 10000,
            "loan_amount_requested": 500000, "loan_tenure_months": 24,
        },
    },
    {
        "name": "Profile 9 — Tier-3 City Applicant",
        "profile": {
            "age": 32, "monthly_net_income": 35000, "employer_type": "Private",
            "employment_tenure_months": 24, "city_tier": "Tier3",
            "cibil_score": 700, "existing_emi_monthly": 5000,
            "loan_amount_requested": 150000, "loan_tenure_months": 36,
        },
    },
    {
        "name": "Profile 10 — Low Income (₹12,000/month)",
        "profile": {
            "age": 25, "monthly_net_income": 12000, "employer_type": "Private",
            "employment_tenure_months": 18, "city_tier": "Tier2",
            "cibil_score": 650, "existing_emi_monthly": 0,
            "loan_amount_requested": 50000, "loan_tenure_months": 18,
        },
    },
]


def run_tests():
    sys.stdout.reconfigure(encoding='utf-8')
    print("=" * 70)
    print("PERSONAL LOAN ELIGIBILITY MODEL - TEST RESULTS")
    print("=" * 70)

    for test in TEST_PROFILES:
        print(f"\n{test['name']}")
        print("-" * 60)
        result = check_eligibility(test['profile'])

        if result['eligible']:
            print(f"  STATUS     : ELIGIBLE — {result['approving_lenders_count']} lender(s) approve")
            best = result['best_option']
            print(f"  BEST OPTION: {best['lender']}")
            print(f"    Max Loan  : ₹{best['max_loan_amount']:,}")
            print(f"    Rate      : {best['likely_rate_pct']}% p.a.")
            print(f"    EMI       : ₹{best['estimated_emi']:,}/month")
            print(f"    Tenure    : {best['tenure_months']} months")
            print(f"  ALL APPROVALS:")
            for l in result['approving_lenders']:
                print(f"    - {l['lender']:25s} | ₹{l['max_loan_amount']:>10,} | {l['likely_rate_pct']}% | EMI ₹{l['estimated_emi']:,}")
        else:
            print(f"  STATUS : NOT ELIGIBLE")
            # Show which lenders rejected and why
            shown = set()
            for rl in result['rejected_lenders']:
                for reason in rl['rejection_reasons']:
                    if reason not in shown:
                        print(f"  REASON : {reason}")
                        shown.add(reason)

    print("\n" + "=" * 70)


if __name__ == '__main__':
    run_tests()
