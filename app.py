"""
Rental Property Analysis Tool - Streamlit UI with Investment Calculator
"""
import streamlit as st
import pandas as pd
import numpy as np
from api_functions import RealEstateAPI, FRESNO_ZILLOW_URLS
from analysis import (
    calculate_monthly_cash_flow,
    calculate_break_even_down_payment,
    normalize_zillow_data,
    normalize_redfin_data
)


# Page configuration
st.set_page_config(
    page_title="Rental Property Analyzer",
    page_icon="🏠",
    layout="wide"
)

# Initialize session state
if 'listings_data' not in st.session_state:
    st.session_state.listings_data = None
if 'analysis_data' not in st.session_state:
    st.session_state.analysis_data = None
if 'repairs' not in st.session_state:
    st.session_state.repairs = []


def calculate_investment_projections(
    purchase_price, down_payment_pct, interest_rate, loan_years,
    monthly_insurance, annual_tax_rate, monthly_rent, vacancy_rate,
    annual_appreciation, annual_rent_increase, holding_years,
    initial_repairs, ongoing_maintenance_pct, extra_payment_monthly=0,
    cashflow_to_principal_pct=0
):
    """
    Calculate year-by-year investment projections.

    Args:
        extra_payment_monthly: Fixed extra monthly payment to principal
        cashflow_to_principal_pct: Percentage of positive cash flow to apply to principal (0-1)

    Returns DataFrame with yearly metrics.
    """
    projections = []

    # Initial calculations
    down_payment = purchase_price * down_payment_pct
    loan_amount = purchase_price - down_payment
    monthly_rate = interest_rate / 12
    total_months = loan_years * 12

    # Monthly mortgage payment
    if interest_rate > 0:
        monthly_mortgage = (loan_amount * (monthly_rate * (1 + monthly_rate) ** total_months)) / \
                          (((1 + monthly_rate) ** total_months) - 1)
    else:
        monthly_mortgage = loan_amount / total_months

    # Starting values
    current_property_value = purchase_price
    current_monthly_rent = monthly_rent
    remaining_balance = loan_amount
    total_cash_invested = down_payment + initial_repairs
    cumulative_cash_flow = 0
    cumulative_extra_principal = 0

    for year in range(1, holding_years + 1):
        # Calculate for this year
        year_start_balance = remaining_balance

        # Annual appreciation
        if year > 1:
            current_property_value *= (1 + annual_appreciation)
            current_monthly_rent *= (1 + annual_rent_increase)

        # Monthly calculations
        monthly_property_tax = (current_property_value * annual_tax_rate) / 12
        monthly_maintenance = (purchase_price * ongoing_maintenance_pct) / 12

        # Effective rent (accounting for vacancy)
        effective_monthly_rent = current_monthly_rent * (1 - vacancy_rate)

        # Monthly cash flow BEFORE extra principal
        monthly_expenses = monthly_mortgage + monthly_property_tax + monthly_insurance + monthly_maintenance
        monthly_cash_flow_gross = effective_monthly_rent - monthly_expenses

        # Loan paydown for the year with extra principal payments
        principal_paid = 0
        total_extra_principal_this_year = 0
        temp_balance = year_start_balance

        for month in range(12):
            if temp_balance > 0:
                # Regular mortgage payment
                interest_payment = temp_balance * monthly_rate
                principal_payment = monthly_mortgage - interest_payment

                # Extra principal from fixed monthly amount
                extra_from_fixed = extra_payment_monthly

                # Extra principal from cash flow (calculated each month based on current cash flow)
                extra_from_cashflow = 0
                if monthly_cash_flow_gross > 0:
                    extra_from_cashflow = monthly_cash_flow_gross * cashflow_to_principal_pct

                # Total extra principal this month
                total_extra = extra_from_fixed + extra_from_cashflow

                # Don't pay more than remaining balance
                total_extra = min(total_extra, temp_balance - principal_payment)

                # Update running totals
                principal_paid += principal_payment + total_extra
                total_extra_principal_this_year += total_extra
                temp_balance -= (principal_payment + total_extra)

                if temp_balance < 0:
                    temp_balance = 0

        remaining_balance = temp_balance
        cumulative_extra_principal += total_extra_principal_this_year

        # Adjust cash flow for money sent to extra principal
        annual_cash_flow = (monthly_cash_flow_gross * 12) - total_extra_principal_this_year
        monthly_cash_flow = annual_cash_flow / 12

        # Equity
        equity = current_property_value - remaining_balance

        # Cumulative cash flow (what you actually receive)
        cumulative_cash_flow += annual_cash_flow

        # Total cash invested (including extra principal payments)
        total_cash_invested_adjusted = total_cash_invested + cumulative_extra_principal

        # ROI and Cash-on-Cash Return
        total_return = cumulative_cash_flow + equity - total_cash_invested_adjusted
        roi_pct = (total_return / total_cash_invested_adjusted * 100) if total_cash_invested_adjusted > 0 else 0
        cash_on_cash = (annual_cash_flow / total_cash_invested * 100) if total_cash_invested > 0 else 0

        # Net profit if sold today
        selling_costs = current_property_value * 0.06  # 6% selling costs
        net_proceeds = current_property_value - remaining_balance - selling_costs
        total_profit = net_proceeds + cumulative_cash_flow - total_cash_invested_adjusted

        # Interest saved by paying extra principal
        # This is a simplified calculation - actual savings compound over time

        projections.append({
            'Year': year,
            'PropertyValue': round(current_property_value, 2),
            'MonthlyRent': round(current_monthly_rent, 2),
            'MonthlyCashFlow': round(monthly_cash_flow, 2),
            'AnnualCashFlow': round(annual_cash_flow, 2),
            'CumulativeCashFlow': round(cumulative_cash_flow, 2),
            'LoanBalance': round(remaining_balance, 2),
            'PrincipalPaid': round(principal_paid, 2),
            'ExtraPrincipalThisYear': round(total_extra_principal_this_year, 2),
            'CumulativeExtraPrincipal': round(cumulative_extra_principal, 2),
            'Equity': round(equity, 2),
            'CashOnCashReturn': round(cash_on_cash, 2),
            'TotalROI': round(roi_pct, 2),
            'NetProceedsIfSold': round(net_proceeds, 2),
            'TotalProfit': round(total_profit, 2)
        })

    return pd.DataFrame(projections)


def render_investment_calculator():
    """Render the Investment Calculator tab."""
    st.header("🏡 Individual Property Investment Calculator")
    st.markdown("Analyze a specific property with detailed projections and ROI calculations")

    # Two columns for inputs
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Property Details")
        property_name = st.text_input("Property Name/Address", "123 Main St")
        purchase_price = st.number_input(
            "Purchase Price ($)",
            min_value=0,
            value=500000,
            step=10000,
            format="%d"
        )

        st.subheader("Financing")
        down_payment_pct = st.slider(
            "Down Payment (%)",
            min_value=0,
            max_value=100,
            value=20,
            step=5
        ) / 100

        interest_rate = st.number_input(
            "Interest Rate (%)",
            min_value=0.0,
            max_value=15.0,
            value=6.5,
            step=0.1
        ) / 100

        loan_years = st.number_input(
            "Loan Term (years)",
            min_value=10,
            max_value=30,
            value=30,
            step=5
        )

        st.subheader("Monthly Expenses")
        monthly_insurance = st.number_input(
            "Monthly Insurance ($)",
            min_value=0,
            value=150,
            step=25
        )

        annual_tax_rate = st.number_input(
            "Annual Property Tax Rate (%)",
            min_value=0.0,
            max_value=5.0,
            value=1.25,
            step=0.05
        ) / 100

        ongoing_maintenance_pct = st.number_input(
            "Ongoing Maintenance (% of purchase price annually)",
            min_value=0.0,
            max_value=10.0,
            value=1.0,
            step=0.25,
            help="Typical is 1-2% of property value per year"
        ) / 100

        st.subheader("Extra Principal Payments")

        extra_payment_monthly = st.number_input(
            "Fixed Extra Monthly Payment ($)",
            min_value=0,
            value=0,
            step=100,
            help="Additional fixed amount to pay toward principal each month"
        )

        cashflow_to_principal_pct = st.slider(
            "% of Positive Cash Flow to Principal",
            min_value=0,
            max_value=100,
            value=0,
            step=5,
            help="Automatically apply this percentage of positive cash flow to extra principal"
        ) / 100

        if cashflow_to_principal_pct > 0:
            st.info(f"💡 {cashflow_to_principal_pct*100:.0f}% of positive cash flow will be applied to principal, reducing your actual cash flow but building equity faster!")

    with col2:
        st.subheader("Income")
        monthly_rent = st.number_input(
            "Monthly Rent ($)",
            min_value=0,
            value=3000,
            step=100
        )

        vacancy_rate = st.number_input(
            "Vacancy Rate (%)",
            min_value=0.0,
            max_value=50.0,
            value=5.0,
            step=1.0,
            help="Percentage of time property sits vacant"
        ) / 100

        st.subheader("Projections")
        holding_years = st.slider(
            "Holding Period (years)",
            min_value=1,
            max_value=30,
            value=10,
            step=1
        )

        annual_appreciation = st.number_input(
            "Annual Property Appreciation (%)",
            min_value=-10.0,
            max_value=20.0,
            value=3.0,
            step=0.5
        ) / 100

        annual_rent_increase = st.number_input(
            "Annual Rent Increase (%)",
            min_value=-10.0,
            max_value=20.0,
            value=2.5,
            step=0.5
        ) / 100

        st.subheader("Initial Repairs/Renovations")

        # Repair calculator
        st.markdown("#### Add Repairs")

        repair_col1, repair_col2, repair_col3 = st.columns([2, 2, 1])

        with repair_col1:
            room_options = [
                "Kitchen", "Bathroom", "Bedroom", "Living Room",
                "Dining Room", "Basement", "Attic", "Roof",
                "HVAC", "Plumbing", "Electrical", "Exterior",
                "Flooring", "Paint", "Landscaping", "Other"
            ]
            repair_room = st.selectbox("Room/Area", room_options, key="repair_room")

        with repair_col2:
            repair_description = st.text_input("Description", key="repair_desc", placeholder="e.g., New countertops")

        with repair_col3:
            repair_cost = st.number_input("Cost ($)", min_value=0, value=0, step=100, key="repair_cost")

        if st.button("➕ Add Repair"):
            if repair_cost > 0:
                st.session_state.repairs.append({
                    'Room': repair_room,
                    'Description': repair_description,
                    'Cost': repair_cost
                })
                st.rerun()

        # Display current repairs
        if st.session_state.repairs:
            st.markdown("#### Repair List")

            # Display repairs with remove buttons
            for idx, repair in enumerate(st.session_state.repairs):
                col_room, col_desc, col_cost, col_remove = st.columns([2, 3, 2, 1])
                with col_room:
                    st.text(repair['Room'])
                with col_desc:
                    st.text(repair['Description'])
                with col_cost:
                    st.text(f"${repair['Cost']:,.0f}")
                with col_remove:
                    if st.button("🗑️", key=f"remove_{idx}", help="Remove this repair"):
                        st.session_state.repairs.pop(idx)
                        st.rerun()

            total_repairs = sum([r['Cost'] for r in st.session_state.repairs])
            st.metric("Total Repair Costs", f"${total_repairs:,.0f}")

            if st.button("🗑️ Clear All Repairs"):
                st.session_state.repairs = []
                st.rerun()
        else:
            total_repairs = 0
            st.info("No repairs added yet")

    # Calculate button
    st.markdown("---")
    if st.button("📊 Calculate Investment Projections", type="primary", use_container_width=True):

        # Calculate projections
        projections_df = calculate_investment_projections(
            purchase_price=purchase_price,
            down_payment_pct=down_payment_pct,
            interest_rate=interest_rate,
            loan_years=loan_years,
            monthly_insurance=monthly_insurance,
            annual_tax_rate=annual_tax_rate,
            monthly_rent=monthly_rent,
            vacancy_rate=vacancy_rate,
            annual_appreciation=annual_appreciation,
            annual_rent_increase=annual_rent_increase,
            holding_years=holding_years,
            initial_repairs=total_repairs,
            ongoing_maintenance_pct=ongoing_maintenance_pct,
            extra_payment_monthly=extra_payment_monthly,
            cashflow_to_principal_pct=cashflow_to_principal_pct
        )

        # Display summary metrics
        st.markdown("---")
        st.subheader("📈 Investment Summary")
        final_year = projections_df.iloc[-1]
        # Show extra principal impact if applicable
        if extra_payment_monthly > 0 or cashflow_to_principal_pct > 0:
            total_extra_principal = final_year['CumulativeExtraPrincipal']
            st.info(f"💰 Extra Principal Payments: ${total_extra_principal:,.0f} over {holding_years} years - This accelerated your loan payoff and built ${total_extra_principal:,.0f} in additional equity!")

        # Key metrics at the top
        metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

        down_payment_amount = purchase_price * down_payment_pct
        total_invested = down_payment_amount + total_repairs
        final_year = projections_df.iloc[-1]

        with metric_col1:
            st.metric("Total Cash Invested", f"${total_invested:,.0f}")
        with metric_col2:
            st.metric(
                f"Year {holding_years} Property Value",
                f"${final_year['PropertyValue']:,.0f}",
                delta=f"+${final_year['PropertyValue'] - purchase_price:,.0f}"
            )
        with metric_col3:
            st.metric(
                "Total Profit (if sold)",
                f"${final_year['TotalProfit']:,.0f}",
                delta=f"{final_year['TotalROI']:.1f}% ROI"
            )
        with metric_col4:
            st.metric(
                f"Year {holding_years} Monthly Rent",
                f"${final_year['MonthlyRent']:,.0f}",
                delta=f"+${final_year['MonthlyRent'] - monthly_rent:,.0f}"
            )

        # Year-by-year projection table
        st.markdown("---")
        st.subheader("📅 Year-by-Year Projections")

        # Format the dataframe for display
        display_df = projections_df.copy()
        display_df['PropertyValue'] = display_df['PropertyValue'].apply(lambda x: f"${x:,.0f}")
        display_df['MonthlyRent'] = display_df['MonthlyRent'].apply(lambda x: f"${x:,.0f}")
        display_df['MonthlyCashFlow'] = display_df['MonthlyCashFlow'].apply(lambda x: f"${x:,.0f}")
        display_df['AnnualCashFlow'] = display_df['AnnualCashFlow'].apply(lambda x: f"${x:,.0f}")
        display_df['CumulativeCashFlow'] = display_df['CumulativeCashFlow'].apply(lambda x: f"${x:,.0f}")
        display_df['LoanBalance'] = display_df['LoanBalance'].apply(lambda x: f"${x:,.0f}")
        display_df['PrincipalPaid'] = display_df['PrincipalPaid'].apply(lambda x: f"${x:,.0f}")
        display_df['ExtraPrincipalThisYear'] = display_df['ExtraPrincipalThisYear'].apply(lambda x: f"${x:,.0f}")
        display_df['CumulativeExtraPrincipal'] = display_df['CumulativeExtraPrincipal'].apply(lambda x: f"${x:,.0f}")
        display_df['Equity'] = display_df['Equity'].apply(lambda x: f"${x:,.0f}")
        display_df['CashOnCashReturn'] = display_df['CashOnCashReturn'].apply(lambda x: f"{x:.2f}%")
        display_df['TotalROI'] = display_df['TotalROI'].apply(lambda x: f"{x:.2f}%")
        display_df['TotalProfit'] = display_df['TotalProfit'].apply(lambda x: f"${x:,.0f}")

        st.dataframe(display_df, use_container_width=True, hide_index=True)

        # Charts
        st.markdown("---")
        st.subheader("📊 Visual Projections")

        chart_tab1, chart_tab2, chart_tab3, chart_tab4 = st.tabs([
            "Property Value & Equity",
            "Cash Flow",
            "Loan Paydown",
            "ROI Metrics"
        ])

        with chart_tab1:
            st.markdown("#### Property Value vs Equity Growth")
            chart_data = projections_df[['Year', 'PropertyValue', 'Equity', 'LoanBalance']].set_index('Year')
            st.line_chart(chart_data)

        with chart_tab2:
            st.markdown("#### Cash Flow Projections")
            chart_data = projections_df[['Year', 'MonthlyCashFlow', 'AnnualCashFlow', 'CumulativeCashFlow']].set_index('Year')
            st.line_chart(chart_data)

        with chart_tab3:
            st.markdown("#### Loan Balance Reduction")
            chart_data = projections_df[['Year', 'LoanBalance']].set_index('Year')
            st.area_chart(chart_data)

        with chart_tab4:
            st.markdown("#### Return on Investment")
            chart_data = projections_df[['Year', 'CashOnCashReturn', 'TotalROI']].set_index('Year')
            st.line_chart(chart_data)

        # Download options
        st.markdown("---")
        col1, col2 = st.columns(2)

        with col1:
            csv = projections_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Projections (CSV)",
                data=csv,
                file_name=f"{property_name.replace(' ', '_')}_projections.csv",
                mime="text/csv"
            )

        with col2:
            if st.session_state.repairs:
                repairs_csv = pd.DataFrame(st.session_state.repairs).to_csv(index=False)
                st.download_button(
                    label="📥 Download Repairs List (CSV)",
                    data=repairs_csv,
                    file_name=f"{property_name.replace(' ', '_')}_repairs.csv",
                    mime="text/csv"
                )


def main():
    st.title("🏠 Rental Property Investment Analyzer")
    st.markdown("Analyze potential rental properties and calculate cash flow projections")

    # Sidebar for inputs
    with st.sidebar:
        st.header("Settings")

        # API Selection
        data_source = st.selectbox(
            "Data Source",
            ["Zillow (Scrapeak)", "Zillow (Working API)", "Redfin"]
        )

        # URL Input
        st.subheader("Property Search")

        # Quick select for Fresno zip codes
        if data_source.startswith("Zillow"):
            use_preset = st.checkbox("Use Fresno ZIP Code Presets")

            if use_preset:
                selected_zip = st.selectbox(
                    "Select ZIP Code",
                    list(FRESNO_ZILLOW_URLS.keys())
                )
                listing_url = FRESNO_ZILLOW_URLS[selected_zip]
                st.text_input("URL", value=listing_url, disabled=True, key="preset_url")
            else:
                listing_url = st.text_input(
                    "Listing URL",
                    placeholder="Paste Zillow or Redfin URL here"
                )
        else:
            listing_url = st.text_input(
                "Listing URL",
                placeholder="Paste Redfin URL here"
            )

        # Financial Parameters
        st.subheader("Financial Parameters")

        interest_rate = st.number_input(
            "Interest Rate (%)",
            min_value=0.0,
            max_value=15.0,
            value=6.1,
            step=0.1,
            help="Annual interest rate for the mortgage"
        ) / 100

        loan_years = st.number_input(
            "Loan Term (years)",
            min_value=10,
            max_value=30,
            value=30,
            step=5
        )

        down_payment = st.number_input(
            "Down Payment (%)",
            min_value=0.0,
            max_value=100.0,
            value=20.0,
            step=5.0,
            help="Down payment percentage"
        ) / 100

        monthly_insurance = st.number_input(
            "Monthly Insurance ($)",
            min_value=0,
            max_value=1000,
            value=100,
            step=50
        )

        # Default rent estimate
        default_rent = st.number_input(
            "Default Rent Estimate ($)",
            min_value=0,
            max_value=20000,
            value=3000,
            step=100,
            help="Used when property doesn't have a rent estimate"
        )

        # Fetch button
        fetch_button = st.button("🔍 Fetch Listings", type="primary", use_container_width=True)

    # Main content area
    if fetch_button and listing_url:
        with st.spinner("Fetching property listings..."):
            try:
                api = RealEstateAPI()

                # Fetch data based on source
                if data_source == "Zillow (Scrapeak)":
                    df = api.get_zillow_listings(listing_url)
                    df = normalize_zillow_data(df)
                elif data_source == "Zillow (Working API)":
                    df = api.get_zillow_by_working_api(listing_url)
                    df = normalize_zillow_data(df)
                else:  # Redfin
                    df = api.get_redfin_listings(listing_url)
                    df = normalize_redfin_data(df)

                if df.empty:
                    st.error("No listings found. Please check the URL and try again.")
                    return

                # Fill missing rent estimates
                if 'RentEstimate' in df.columns:
                    df['RentEstimate'] = df['RentEstimate'].fillna(default_rent)
                else:
                    df['RentEstimate'] = default_rent

                st.session_state.listings_data = df
                st.success(f"✅ Fetched {len(df)} properties")

            except Exception as e:
                st.error(f"Error fetching data: {str(e)}")
                return

    # Display and analyze data
    if st.session_state.listings_data is not None:
        df = st.session_state.listings_data

        # Tabs for different views
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Property Listings",
            "💰 Cash Flow Analysis",
            "📈 Break-Even Analysis",
            "🏡 Investment Calculator"
        ])

        with tab1:
            st.subheader("Property Listings")
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )

            # Summary statistics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Properties", len(df))
            with col2:
                st.metric("Avg Price", f"${df['Price'].mean():,.0f}")
            with col3:
                if 'Sqft' in df.columns:
                    avg_sqft = df['Sqft'].replace('', np.nan).astype(float).mean()
                    st.metric("Avg Sqft", f"{avg_sqft:,.0f}" if not pd.isna(avg_sqft) else "N/A")
            with col4:
                st.metric("Avg Rent Est.", f"${df['RentEstimate'].mean():,.0f}")

        with tab2:
            st.subheader("Monthly Cash Flow Analysis")

            analyze_button = st.button("🔄 Calculate Cash Flow", type="primary")

            if analyze_button:
                with st.spinner("Calculating cash flows..."):
                    analysis_df = calculate_monthly_cash_flow(
                        df,
                        interest_rate,
                        loan_years * 12,
                        monthly_insurance,
                        down_payment
                    )
                    st.session_state.analysis_data = analysis_df

            if st.session_state.analysis_data is not None:
                analysis_df = st.session_state.analysis_data

                # Display results
                st.dataframe(
                    analysis_df,
                    use_container_width=True,
                    hide_index=True
                )

                # Metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    positive_cf = len(analysis_df[analysis_df['MonthlyCashFlow'] > 0])
                    st.metric("Positive Cash Flow", f"{positive_cf} properties")
                with col2:
                    avg_cf = analysis_df['MonthlyCashFlow'].mean()
                    st.metric("Avg Monthly Cash Flow", f"${avg_cf:,.2f}")
                with col3:
                    best_cf = analysis_df['MonthlyCashFlow'].max()
                    st.metric("Best Cash Flow", f"${best_cf:,.2f}")

                # Show best deals
                st.subheader("🌟 Top 5 Best Deals")
                top_5 = analysis_df.head(5)

                for idx, row in top_5.iterrows():
                    with st.expander(f"#{idx + 1}: {row.get('Address', 'N/A')} - ${row['MonthlyCashFlow']:,.2f}/mo"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Price:** ${row['Price']:,.0f}")
                            st.write(f"**Monthly Rent:** ${row['RentEstimate']:,.0f}")
                            st.write(f"**Monthly Mortgage:** ${row['MonthlyMortgage']:,.2f}")
                        with col2:
                            st.write(f"**Property Tax:** ${row['PropertyTax']:,.2f}")
                            st.write(f"**Insurance:** ${monthly_insurance:,.2f}")
                            st.write(f"**Cash Flow:** ${row['MonthlyCashFlow']:,.2f}")

                # Download option
                csv = analysis_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Analysis as CSV",
                    data=csv,
                    file_name="rental_analysis.csv",
                    mime="text/csv"
                )

        with tab3:
            st.subheader("Break-Even Down Payment Analysis")
            st.markdown("Find the minimum down payment needed for positive cash flow on each property")

            breakeven_button = st.button("🔄 Calculate Break-Even", type="primary")

            if breakeven_button:
                if st.session_state.analysis_data is None:
                    st.warning("Please run Cash Flow Analysis first (Tab 2)")
                else:
                    with st.spinner("Calculating break-even down payments..."):
                        breakeven_df = calculate_break_even_down_payment(
                            st.session_state.analysis_data,
                            interest_rate,
                            loan_years * 12,
                            monthly_insurance
                        )

                        if breakeven_df.empty:
                            st.warning("No properties can achieve positive cash flow with available down payments")
                        else:
                            st.dataframe(
                                breakeven_df,
                                use_container_width=True,
                                hide_index=True
                            )

                            # Summary
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                viable = len(breakeven_df)
                                st.metric("Viable Properties", viable)
                            with col2:
                                avg_down = breakeven_df['DownPaymentPercent'].mean() * 100
                                st.metric("Avg Down Payment", f"{avg_down:.1f}%")
                            with col3:
                                at_20 = len(breakeven_df[breakeven_df['DownPaymentPercent'] <= 0.20])
                                st.metric("Profitable at 20%", at_20)

                            # Download
                            csv = breakeven_df.to_csv(index=False)
                            st.download_button(
                                label="📥 Download Break-Even Analysis",
                                data=csv,
                                file_name="breakeven_analysis.csv",
                                mime="text/csv"
                            )

        with tab4:
            render_investment_calculator()

    else:
        # Show Investment Calculator even without fetched listings
        st.info("👈 Enter a property listing URL in the sidebar and click 'Fetch Listings' to analyze multiple properties, or use the Investment Calculator below for individual property analysis")

        # Show Investment Calculator by default
        render_investment_calculator()

        with st.expander("ℹ️ How to use this tool"):
            st.markdown("""
            ### Getting Started
            1. Select your data source (Zillow or Redfin)
            2. Enter a listing URL or use Fresno ZIP code presets
            3. Configure your financial parameters
            4. Click "Fetch Listings"
            
            ### Analysis Features
            - **Property Listings**: View all fetched properties
            - **Cash Flow Analysis**: Calculate monthly cash flow for each property
            - **Break-Even Analysis**: Find minimum down payment for profitability
            - **Investment Calculator**: Detailed projections for individual properties
            
            ### Financial Calculations
            - Monthly mortgage payments using standard amortization
            - Property tax estimated at 1.25% annually
            - Customizable insurance and down payment
            - Rent estimates from Zillow/Redfin or custom values
            - Year-by-year projections with appreciation and rent increases
            """)


if __name__ == "__main__":
    main()
