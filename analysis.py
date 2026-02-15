"""
Rental property financial analysis functions.
"""
import pandas as pd
import numpy as np


def calculate_monthly_cash_flow(df, interest_rate, loan_months=360,
                                monthly_insurance=100, down_payment_percent=0.20):
    """
    Calculate monthly cash flow for rental properties.

    Args:
        df: DataFrame with property data
        interest_rate: Annual interest rate (e.g., 0.061 for 6.1%)
        loan_months: Loan term in months (default: 360 for 30 years)
        monthly_insurance: Monthly insurance cost in dollars
        down_payment_percent: Down payment as decimal (e.g., 0.20 for 20%)

    Returns:
        DataFrame with cash flow calculations added
    """
    df = df.copy()

    # Convert annual rate to monthly
    monthly_rate = interest_rate / 12

    # Amount financed (1 - down payment)
    loan_to_value = 1 - down_payment_percent

    # Calculate monthly property tax (assuming 1.25% annual property tax)
    df["PropertyTax"] = round((df["Price"] * 0.0125) / 12, 2)

    # Calculate monthly mortgage payment using standard mortgage formula
    df["MonthlyMortgage"] = round(
        ((loan_to_value * df["Price"]) *
         (monthly_rate * (1 + monthly_rate) ** loan_months)) /
        (((1 + monthly_rate) ** loan_months) - 1),
        2
    )

    # Calculate monthly cash flow
    df["MonthlyCashFlow"] = round(
        df["RentEstimate"] - (df["PropertyTax"] + df["MonthlyMortgage"] + monthly_insurance),
        2
    )

    # Sort by cash flow (best deals first)
    df = df.sort_values(by=['MonthlyCashFlow'], ascending=False)
    df = df.reset_index(drop=True)

    return df


def calculate_break_even_down_payment(df, interest_rate, loan_months=360,
                                      monthly_insurance=100):
    """
    Calculate the minimum down payment percentage needed for positive cash flow.

    Args:
        df: DataFrame with property data (must have MonthlyCashFlow column)
        interest_rate: Annual interest rate
        loan_months: Loan term in months
        monthly_insurance: Monthly insurance cost

    Returns:
        DataFrame with down payment percentages and amounts
    """
    result_df = pd.DataFrame()
    down_payment_percentages = []

    for idx, row in df.iterrows():
        property_df = pd.DataFrame([row])

        # If already profitable at 20% down
        if row['MonthlyCashFlow'] > 0:
            result_df = pd.concat([result_df, property_df], ignore_index=True)
            down_payment_percentages.append(0.20)
        else:
            # Find minimum down payment for positive cash flow
            found = False
            for down_pct in np.arange(0.20, 1.0, 0.01):
                test_df = calculate_monthly_cash_flow(
                    property_df,
                    interest_rate,
                    loan_months,
                    monthly_insurance,
                    down_pct
                )

                if test_df['MonthlyCashFlow'].iloc[0] > 0:
                    result_df = pd.concat([result_df, test_df], ignore_index=True)
                    down_payment_percentages.append(round(down_pct, 2))
                    found = True
                    break

            # If no viable down payment found, skip this property
            if not found:
                continue

    # Add down payment info
    result_df['DownPaymentPercent'] = down_payment_percentages
    result_df['DownPaymentAmount'] = round(
        result_df['DownPaymentPercent'] * result_df['Price'],
        2
    )

    return result_df


def normalize_zillow_data(df):
    """
    Normalize Zillow API response columns to standard format.

    Args:
        df: Raw DataFrame from Zillow API

    Returns:
        DataFrame with standardized columns
    """
    # Column mapping
    column_mapping = {
        'hdpData.homeInfo.homeType': 'HomeType',
        'hdpData.homeInfo.streetAddress': 'Address',
        'hdpData.homeInfo.city': 'City',
        'hdpData.homeInfo.state': 'State',
        'hdpData.homeInfo.zipcode': 'Zipcode',
        'hdpData.homeInfo.livingArea': 'Sqft',
        'hdpData.homeInfo.lotAreaValue': 'LotSize',
        'hdpData.homeInfo.price': 'Price',
        'hdpData.homeInfo.zestimate': 'PriceEstimate',
        'hdpData.homeInfo.rentZestimate': 'RentEstimate',
        'zpid': 'ID'
    }

    df = df.rename(columns=column_mapping)

    # Select relevant columns
    columns = ['ID', 'Address', 'Zipcode', 'Sqft', 'LotSize',
               'Price', 'PriceEstimate', 'RentEstimate', 'HomeType']

    # Only keep columns that exist
    available_columns = [col for col in columns if col in df.columns]
    df = df[available_columns]

    # Clean data
    df = df.dropna(subset=['Price'])

    # Set data types
    if 'ID' in df.columns:
        df['ID'] = df['ID'].astype(str)
    if 'Address' in df.columns:
        df['Address'] = df['Address'].astype(str)
    if 'Zipcode' in df.columns:
        df['Zipcode'] = df['Zipcode'].astype(str)
    if 'LotSize' in df.columns:
        df['LotSize'] = df['LotSize'].astype(str)
    if 'Price' in df.columns:
        df['Price'] = pd.to_numeric(df['Price'], errors='coerce')
    if 'PriceEstimate' in df.columns:
        df['PriceEstimate'] = pd.to_numeric(df['PriceEstimate'], errors='coerce')
    if 'RentEstimate' in df.columns:
        df['RentEstimate'] = pd.to_numeric(df['RentEstimate'], errors='coerce')

    df = df.dropna(subset=['Price'])

    return df


def normalize_redfin_data(df):
    """
    Normalize Redfin API response columns to standard format.

    Args:
        df: Raw DataFrame from Redfin API

    Returns:
        DataFrame with standardized columns
    """
    column_mapping = {
        'listingId': 'ID',
        'baths': 'Baths',
        'beds': 'Beds',
        'sqFt.value': 'Sqft',
        'streetLine.value': 'Address',
        'zip': 'Zipcode',
        'price.value': 'Price',
        'lotSize.value': 'LotSize'
    }

    df = df.rename(columns=column_mapping)

    columns = ['ID', 'Address', 'Zipcode', 'Beds', 'Baths', 'Sqft', 'LotSize', 'Price']
    available_columns = [col for col in columns if col in df.columns]
    df = df[available_columns]

    # Clean data
    df = df.dropna(subset=['Price'])

    # Set data types
    if 'ID' in df.columns:
        df['ID'] = df['ID'].astype(str)
    if 'Address' in df.columns:
        df['Address'] = df['Address'].astype(str)
    if 'Zipcode' in df.columns:
        df['Zipcode'] = df['Zipcode'].astype(str)
    if 'Beds' in df.columns:
        df['Beds'] = df['Beds'].astype(str)
    if 'Baths' in df.columns:
        df['Baths'] = df['Baths'].astype(str)
    if 'LotSize' in df.columns:
        df['LotSize'] = df['LotSize'].astype(str)
    if 'Price' in df.columns:
        df['Price'] = pd.to_numeric(df['Price'], errors='coerce')

    df = df.dropna(subset=['Price'])

    return df
