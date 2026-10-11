import sys
import os

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(__file__))

from model.eligibility_engine import check_eligibility


def get_int(prompt, min_val=None, max_val=None):
    while True:
        try:
            val = int(input(prompt).strip())
            if min_val is not None and val < min_val:
                print(f"  Please enter a value >= {min_val}")
                continue
            if max_val is not None and val > max_val:
                print(f"  Please enter a value <= {max_val}")
                continue
            return val
        except ValueError:
            print("  Please enter a valid number.")


CITY_TIERS = {
    "Tier1": [
        "Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai",
        "Kolkata", "Pune", "Ahmedabad", "Surat", "Jaipur",
        "Lucknow", "Kanpur", "Nagpur", "Indore", "Thane",
        "Bhopal", "Visakhapatnam", "Pimpri-Chinchwad", "Patna", "Vadodara",
    ],
    "Tier2": [
        "Agra", "Nashik", "Faridabad", "Meerut", "Rajkot",
        "Varanasi", "Srinagar", "Aurangabad", "Dhanbad", "Amritsar",
        "Allahabad", "Ranchi", "Howrah", "Coimbatore", "Jabalpur",
        "Gwalior", "Vijayawada", "Jodhpur", "Madurai", "Raipur",
        "Kota", "Guwahati", "Chandigarh", "Solapur", "Hubli",
        "Mysore", "Tiruchirappalli", "Bareilly", "Aligarh", "Moradabad",
        "Noida", "Gurugram", "Navi Mumbai", "Thane", "Bhubaneswar",
        "Dehradun", "Udaipur", "Jalandhar", "Mangalore", "Kolhapur",
    ],
    "Tier3": [
        "All other cities and towns not listed above",
        "Villages and rural areas",
        "Small towns with population below 1 lakh",
    ],
}


def show_city_tiers():
    print()
    print("  CITY TIER REFERENCE LIST")
    print("  " + "-" * 60)
    print("  TIER 1 — Major metros and large cities (population 10 lakh+):")
    print("  " + ", ".join(CITY_TIERS["Tier1"]))
    print()
    print("  TIER 2 — Medium cities (population 1 lakh to 10 lakh):")
    print("  " + ", ".join(CITY_TIERS["Tier2"]))
    print()
    print("  TIER 3 — Small towns and rural areas (population below 1 lakh):")
    print("  " + ", ".join(CITY_TIERS["Tier3"]))
    print()


def get_choice(prompt, choices):
    choices_display = " / ".join(f"[{i+1}] {c}" for i, c in enumerate(choices))
    while True:
        print(f"  {choices_display}")
        try:
            val = int(input(prompt).strip())
            if 1 <= val <= len(choices):
                return choices[val - 1]
            print(f"  Please enter a number between 1 and {len(choices)}")
        except ValueError:
            print("  Please enter a number.")


def print_separator(char="=", width=65):
    print(char * width)


def collect_profile():
    print_separator()
    print("  PERSONAL LOAN ELIGIBILITY CHECKER")
    print("  Answer the questions below to check your loan eligibility")
    print_separator()
    print()

    age = get_int("Your age (years): ", 18, 80)

    monthly_net_income = get_int("Monthly net income (Rs.): ", 1000)

    print("Employer type:")
    employer_type = get_choice(
        "Select option: ",
        ["Government", "PSU", "MNC", "Private", "Self-Employed"]
    )

    employment_tenure_months = get_int("Months at current job: ", 0)

    cibil_score = get_int("CIBIL score (enter 0 if no credit history): ", 0, 900)

    existing_emi_monthly = get_int("Total existing EMIs per month (Rs., enter 0 if none): ", 0)

    show_city_tiers()
    print("  Which tier is your city? (check the list above)")
    city_tier = get_choice(
        "Select option: ",
        ["Tier1", "Tier2", "Tier3"]
    )

    loan_amount_requested = get_int("Loan amount you need (Rs.): ", 1000)

    loan_tenure_months = get_int("Repayment tenure you want (months): ", 1, 120)

    return {
        "age": age,
        "monthly_net_income": monthly_net_income,
        "employer_type": employer_type,
        "employment_tenure_months": employment_tenure_months,
        "city_tier": city_tier,
        "cibil_score": cibil_score,
        "existing_emi_monthly": existing_emi_monthly,
        "loan_amount_requested": loan_amount_requested,
        "loan_tenure_months": loan_tenure_months,
    }


def display_result(result):
    print()
    print_separator()

    if not result['eligible']:
        print("  RESULT: NOT ELIGIBLE")
        print_separator()
        print()
        print("  Your profile was rejected by all 20 lenders.")
        print("  Common reasons:")
        seen = set()
        for rl in result['rejected_lenders']:
            for reason in rl['rejection_reasons']:
                if reason not in seen:
                    print(f"    - {reason}")
                    seen.add(reason)
        print()
        return

    print(f"  RESULT: ELIGIBLE")
    print(f"  {result['approving_lenders_count']} out of 20 lenders will approve your loan")
    print_separator()

    best = result['best_option']
    print()
    print("  BEST OPTION")
    print_separator("-")
    print(f"  Lender        : {best['lender']}")
    print(f"  Max Loan      : Rs.{best['max_loan_amount']:,}")
    print(f"  Interest Rate : {best['likely_rate_pct']}% per annum")
    print(f"  Monthly EMI   : Rs.{best['estimated_emi']:,}")
    print(f"  Tenure        : {best['tenure_months']} months")
    print(f"  Rate Range    : {best['interest_rate_range']}")
    print(f"  FOIR after    : {best['foir_after_new_loan']}%")
    print()

    print("  ALL APPROVING LENDERS")
    print_separator("-")
    print(f"  {'Lender':<26} {'Max Loan':>12}  {'Rate':>6}  {'EMI/month':>12}")
    print("  " + "-" * 60)
    for l in sorted(result['approving_lenders'], key=lambda x: x['likely_rate_pct']):
        print(
            f"  {l['lender']:<26} "
            f"Rs.{l['max_loan_amount']:>9,}  "
            f"{l['likely_rate_pct']:>5}%  "
            f"Rs.{l['estimated_emi']:>9,}"
        )
    print()

    if len(result['rejected_lenders']) > 0:
        print("  LENDERS THAT REJECTED (and why)")
        print_separator("-")
        for rl in result['rejected_lenders']:
            print(f"  {rl['lender']}")
            for reason in rl['rejection_reasons']:
                print(f"    - {reason}")
        print()

    print_separator()


def main():
    profile = collect_profile()
    print()
    print("  Checking eligibility across 20 lenders...")
    result = check_eligibility(profile)
    display_result(result)


if __name__ == '__main__':
    main()
