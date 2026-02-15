"""
Refactored command-line version of the rental property analyzer.
This maintains the original functionality with cleaner code.
"""
import pandas as pd
from api_functions import RealEstateAPI, FRESNO_ZILLOW_URLS
from analysis import (
    calculate_monthly_cash_flow,
    calculate_break_even_down_payment,
    normalize_zillow_data
)


def main():
    # Configuration
    INTEREST_RATE = 0.061  # 6.1%
    LOAN_MONTHS = 360  # 30 years
    MONTHLY_INSURANCE = 100
    DOWN_PAYMENT = 0.20  # 20%
    DEFAULT_RENT = 12000

    # Example: Fetch Santa Cruz listings
    listing_url = (
        'https://www.zillow.com/santa-cruz-ca/?category=RECENT_SEARCH&searchQueryState='
        '%7B%22pagination%22%3A%7B%7D%2C%22isMapVisible%22%3Atrue%2C%22mapBounds%22%3A'
        '%7B%22west%22%3A-122.02908781704049%2C%22east%22%3A-122.0165350788508%2C'
        '%22south%22%3A36.96246133913433%2C%22north%22%3A36.969182006298986%7D%2C'
        '%22regionSelection%22%3A%5B%7B%22regionId%22%3A13715%2C%22regionType%22%3A6%7D%5D%2C'
        '%22filterState%22%3A%7B%22sort%22%3A%7B%22value%22%3A%22globalrelevanceex%22%7D%2C'
        '%22price%22%3A%7B%22min%22%3A1500000%2C%22max%22%3A1750000%7D%2C%22mp%22%3A%7B'
        '%22min%22%3A7500%2C%22max%22%3A8750%7D%7D%2C%22isListVisible%22%3Atrue%2C'
        '%22mapZoom%22%3A17%2C%22usersSearchTerm%22%3A%22Santa%20Cruz%20CA%22%7D'
    )

    print("Fetching property listings...")
    api = RealEstateAPI()

    # Get listings
    df = api.get_zillow_listings(listing_url)

    if df.empty:
        print("No listings found!")
        return

    # Normalize data
    df = normalize_zillow_data(df)

    # Add rent estimate if missing
    if 'RentEstimate' not in df.columns or df['RentEstimate'].isna().all():
        df['RentEstimate'] = DEFAULT_RENT
    else:
        df['RentEstimate'] = df['RentEstimate'].fillna(DEFAULT_RENT)

    print(f"\n✓ Fetched {len(df)} properties")
    print("\n" + "=" * 80)
    print("PROPERTY LISTINGS")
    print("=" * 80)
    print(df.to_string())

    # Calculate cash flow
    print("\n" + "=" * 80)
    print("CASH FLOW ANALYSIS")
    print("=" * 80)

    cashflow_df = calculate_monthly_cash_flow(
        df,
        INTEREST_RATE,
        LOAN_MONTHS,
        MONTHLY_INSURANCE,
        DOWN_PAYMENT
    )

    print(cashflow_df.to_string())

    # Calculate break-even
    print("\n" + "=" * 80)
    print("BREAK-EVEN DOWN PAYMENT ANALYSIS")
    print("=" * 80)

    breakeven_df = calculate_break_even_down_payment(
        cashflow_df,
        INTEREST_RATE,
        LOAN_MONTHS,
        MONTHLY_INSURANCE
    )

    print(breakeven_df.to_string())

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    positive_cashflow = len(cashflow_df[cashflow_df['MonthlyCashFlow'] > 0])
    avg_cashflow = cashflow_df['MonthlyCashFlow'].mean()
    best_cashflow = cashflow_df['MonthlyCashFlow'].max()

    print(f"Total Properties: {len(df)}")
    print(f"Positive Cash Flow: {positive_cashflow}")
    print(f"Average Monthly Cash Flow: ${avg_cashflow:,.2f}")
    print(f"Best Monthly Cash Flow: ${best_cashflow:,.2f}")

    if not breakeven_df.empty:
        viable_at_20 = len(breakeven_df[breakeven_df['DownPaymentPercent'] <= 0.20])
        print(f"Viable at 20% Down: {viable_at_20}")

    # Optionally save to database
    # from Database import SaveToDatabase
    # SaveToDatabase(cashflow_df)
    # print("\n✓ Saved to database")


if __name__ == "__main__":
    # Configure pandas display options
    pd.set_option("display.max_columns", None)
    pd.set_option("display.max_colwidth", None)
    pd.set_option("display.max_rows", None)
    pd.set_option('display.width', 1000)

    main()
