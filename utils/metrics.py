"""
Metrics Calculation Utilities for ONE Tracker Dashboard
Handles KPI calculations and aggregations
"""

import pandas as pd
from typing import Dict, List, Optional, Tuple
from .sku_utils import add_parent_sku_column

# Performance Thresholds
TARGET_FAIL_RATE = 3.0  # Good month <= 3%
TARGET_REPAIR_RATE = 3.0  # Good month <= 3%
TARGET_ON_TIME_RATE = 97.0  # Required >= 97%
MIN_UNITS_FOR_RATE = 10  # Minimum units for rate calculations
SKU_CONCENTRATION_THRESHOLD = 50.0  # Alert if inspector has > 50% of a SKU
MIN_SKU_VOLUME_FOR_CONCENTRATION = 10  # Only check SKUs with 10+ orders
RECURRING_SKU_MIN_APPEARANCES = 3  # Must appear 3+ of last 6 months
RECURRING_SKU_LOOKBACK_MONTHS = 6


def calculate_summary_metrics(df: pd.DataFrame) -> Dict:
    """
    Calculate high-level summary metrics from SS data.

    Args:
        df: DataFrame with SS stream data

    Returns:
        Dictionary of summary metrics
    """
    total_quantity = df['Quantity'].sum()
    total_final = df['Final_Qty'].sum()
    total_repairs = df['Repairs'].sum()
    total_scrap = df['Scrap'].sum()
    total_qc_fail = df['QC_Fail'].sum()
    total_sewing_fail = df['Sewing_Fail'].sum()
    # Total fails = Scrap (failed items are scrapped)
    # QC_Fail and Sewing_Fail track WHERE the fail was caught, not additional fails
    total_fails = total_scrap
    total_orders = df['Order_Number'].nunique()
    total_red_flags = (df['Red_Flag'] == 'X').sum()

    # Calculate rates (avoid division by zero)
    pass_rate = (total_final / total_quantity * 100) if total_quantity > 0 else 0
    fail_rate = (total_scrap / total_quantity * 100) if total_quantity > 0 else 0
    repair_rate = (total_repairs / total_quantity * 100) if total_quantity > 0 else 0
    scrap_rate = (total_scrap / total_quantity * 100) if total_quantity > 0 else 0

    # Defect detection rate (what % of fails caught at sewing vs QC)
    # Use total_scrap as denominator since that's the actual fail count
    sewing_detection_rate = (total_sewing_fail / total_scrap * 100) if total_scrap > 0 else 0

    return {
        'total_inspected': total_quantity,
        'total_passed': total_final,
        'total_repairs': total_repairs,
        'total_scrap': total_scrap,
        'total_qc_fails': total_qc_fail,
        'total_sewing_fails': total_sewing_fail,
        'total_fails': total_fails,
        'total_orders': total_orders,
        'total_red_flags': total_red_flags,
        'pass_rate': pass_rate,
        'fail_rate': fail_rate,
        'repair_rate': repair_rate,
        'scrap_rate': scrap_rate,
        'sewing_detection_rate': sewing_detection_rate
    }


def get_problem_skus(df: pd.DataFrame, top_n: int = 5, min_volume: int = 10) -> pd.DataFrame:
    """
    Identify problem SKUs based on fail count and fail rate.

    Args:
        df: DataFrame with SS stream data
        top_n: Number of top SKUs to return
        min_volume: Minimum quantity threshold for fail rate ranking

    Returns:
        DataFrame with problem SKU analysis
    """
    # Add parent SKU
    df = add_parent_sku_column(df, 'SKU')

    # Aggregate by parent SKU
    sku_stats = df.groupby('Parent_SKU').agg({
        'Quantity': 'sum',
        'Final_Qty': 'sum',
        'Repairs': 'sum',
        'Scrap': 'sum',
        'QC_Fail': 'sum',
        'Sewing_Fail': 'sum'
    }).reset_index()

    # Calculate metrics
    # Total_Fails = Scrap (failed items are scrapped)
    sku_stats['Total_Fails'] = sku_stats['Scrap']
    sku_stats['Fail_Rate'] = (sku_stats['Scrap'] / sku_stats['Quantity'] * 100).round(2)
    sku_stats['Repair_Rate'] = (sku_stats['Repairs'] / sku_stats['Quantity'] * 100).round(2)

    # Filter by minimum volume for fail rate ranking
    sku_with_volume = sku_stats[sku_stats['Quantity'] >= min_volume].copy()

    # Get top by fail count
    top_by_count = sku_stats.nlargest(top_n, 'Total_Fails')[
        ['Parent_SKU', 'Quantity', 'Total_Fails', 'Fail_Rate', 'Repairs', 'Repair_Rate']
    ].copy()
    top_by_count['Rank_Type'] = 'By Fail Count'

    # Get top by fail rate (with volume threshold)
    top_by_rate = sku_with_volume.nlargest(top_n, 'Fail_Rate')[
        ['Parent_SKU', 'Quantity', 'Total_Fails', 'Fail_Rate', 'Repairs', 'Repair_Rate']
    ].copy()
    top_by_rate['Rank_Type'] = 'By Fail Rate'

    return top_by_count, top_by_rate


def get_top_repair_skus(df: pd.DataFrame, top_n: int = 5, min_volume: int = 10) -> pd.DataFrame:
    """
    Identify SKUs with highest repair counts and rates.

    Args:
        df: DataFrame with SS stream data
        top_n: Number of top SKUs to return
        min_volume: Minimum quantity threshold for rate ranking

    Returns:
        DataFrame with top repair SKUs
    """
    df = add_parent_sku_column(df, 'SKU')

    sku_stats = df.groupby('Parent_SKU').agg({
        'Quantity': 'sum',
        'Repairs': 'sum'
    }).reset_index()

    sku_stats['Repair_Rate'] = (sku_stats['Repairs'] / sku_stats['Quantity'] * 100).round(2)

    # Filter by minimum volume
    sku_with_volume = sku_stats[sku_stats['Quantity'] >= min_volume]

    return sku_with_volume.nlargest(top_n, 'Repairs')[
        ['Parent_SKU', 'Quantity', 'Repairs', 'Repair_Rate']
    ]


def get_inspector_performance(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate performance metrics by inspector.

    Args:
        df: DataFrame with SS stream data

    Returns:
        DataFrame with inspector performance metrics
    """
    inspector_stats = df.groupby('Inspector').agg({
        'Quantity': 'sum',
        'Final_Qty': 'sum',
        'Repairs': 'sum',
        'Scrap': 'sum',
        'QC_Fail': 'sum',
        'Sewing_Fail': 'sum',
        'Order_Number': 'nunique',
        'Red_Flag': lambda x: (x == 'X').sum()
    }).reset_index()

    inspector_stats.columns = ['Inspector', 'Quantity', 'Final_Qty', 'Repairs',
                               'Scrap', 'QC_Fail', 'Sewing_Fail', 'Orders', 'Red_Flags']

    # Calculate rates
    inspector_stats['Pass_Rate'] = (inspector_stats['Final_Qty'] / inspector_stats['Quantity'] * 100).round(2)
    # Total_Fails = Scrap (failed items are scrapped)
    inspector_stats['Total_Fails'] = inspector_stats['Scrap']

    # Sort by quantity (most active first)
    inspector_stats = inspector_stats.sort_values('Quantity', ascending=False)

    return inspector_stats


def get_monthly_trends(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate monthly trend metrics.

    Args:
        df: DataFrame with SS stream data (must have 'Month' column)

    Returns:
        DataFrame with monthly metrics
    """
    # Define month order for sorting
    month_order = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
                   'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']

    monthly_stats = df.groupby('Month').agg({
        'Quantity': 'sum',
        'Final_Qty': 'sum',
        'Repairs': 'sum',
        'Scrap': 'sum',
        'QC_Fail': 'sum',
        'Sewing_Fail': 'sum',
        'Order_Number': 'nunique'
    }).reset_index()

    # Calculate rates
    monthly_stats['Pass_Rate'] = (monthly_stats['Final_Qty'] / monthly_stats['Quantity'] * 100).round(2)
    monthly_stats['Fail_Rate'] = (monthly_stats['Scrap'] / monthly_stats['Quantity'] * 100).round(2)
    monthly_stats['Repair_Rate'] = (monthly_stats['Repairs'] / monthly_stats['Quantity'] * 100).round(2)
    # Total_Fails = Scrap (failed items are scrapped)
    monthly_stats['Total_Fails'] = monthly_stats['Scrap']

    # Sort by month/year
    def month_sort_key(month_str):
        month = month_str[:3]
        year = int(month_str[3:])
        month_num = month_order.index(month) if month in month_order else 0
        return (year, month_num)

    monthly_stats['sort_key'] = monthly_stats['Month'].apply(month_sort_key)
    monthly_stats = monthly_stats.sort_values('sort_key').drop('sort_key', axis=1)

    return monthly_stats


def get_red_flag_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """
    Analyze Red Flag (customer return) patterns.

    Args:
        df: DataFrame with SS stream data

    Returns:
        DataFrame with Red Flag analysis by SKU
    """
    # Filter to only red flagged orders
    red_flags = df[df['Red_Flag'] == 'X'].copy()

    if red_flags.empty:
        return pd.DataFrame(columns=['Parent_SKU', 'Red_Flag_Count', 'Orders'])

    red_flags = add_parent_sku_column(red_flags, 'SKU')

    flag_stats = red_flags.groupby('Parent_SKU').agg({
        'Order_Number': 'nunique',
        'Red_Flag': 'count'
    }).reset_index()

    flag_stats.columns = ['Parent_SKU', 'Orders', 'Red_Flag_Count']
    flag_stats = flag_stats.sort_values('Red_Flag_Count', ascending=False)

    return flag_stats


def generate_insights(metrics: Dict, problem_skus: Tuple, inspector_df: pd.DataFrame) -> List[str]:
    """
    Generate automated insights based on metrics.

    Args:
        metrics: Dictionary of summary metrics
        problem_skus: Tuple of (top by count, top by rate) DataFrames
        inspector_df: Inspector performance DataFrame

    Returns:
        List of insight strings
    """
    insights = []

    # Pass rate insight
    if metrics['pass_rate'] >= 98:
        insights.append(f"✅ Excellent pass rate of {metrics['pass_rate']:.1f}%")
    elif metrics['pass_rate'] >= 95:
        insights.append(f"⚠️ Pass rate at {metrics['pass_rate']:.1f}% - room for improvement")
    else:
        insights.append(f"🔴 Pass rate of {metrics['pass_rate']:.1f}% needs attention")

    # Sewing detection insight
    if metrics['sewing_detection_rate'] >= 70:
        insights.append(f"✅ {metrics['sewing_detection_rate']:.0f}% of defects caught at sewing (good early detection)")
    elif metrics['sewing_detection_rate'] >= 50:
        insights.append(f"⚠️ Only {metrics['sewing_detection_rate']:.0f}% of defects caught at sewing")
    else:
        insights.append(f"🔴 Only {metrics['sewing_detection_rate']:.0f}% caught at sewing - most defects reaching QC")

    # Red flags insight
    if metrics['total_red_flags'] > 0:
        insights.append(f"🚩 {metrics['total_red_flags']} customer returns (Red Flags) this period")

    # Problem SKUs insight
    top_by_count, top_by_rate = problem_skus
    if not top_by_rate.empty:
        high_fail_count = len(top_by_rate[top_by_rate['Fail_Rate'] > 5])
        if high_fail_count > 0:
            insights.append(f"⚠️ {high_fail_count} SKUs have >5% fail rate - review manufacturing")

    # Repair rate insight
    if metrics['repair_rate'] > 5:
        insights.append(f"🔧 High repair rate of {metrics['repair_rate']:.1f}% - rework overhead concern")

    return insights


def calculate_on_time_metrics(df: pd.DataFrame) -> Dict:
    """
    Calculate on-time delivery metrics.

    Args:
        df: DataFrame with Due_Date and Finished_Date columns

    Returns:
        Dictionary with on-time delivery metrics
    """
    # Filter to orders with valid Due_Date
    valid_df = df[df['Due_Date'].notna()].copy()
    orders_missing_due_date = len(df) - len(valid_df)
    orders_with_due_date = len(valid_df)

    if orders_with_due_date == 0:
        return {
            'on_time_rate': 0.0,
            'total_late_orders': 0,
            'total_days_late': 0,
            'avg_days_late': 0.0,
            'orders_missing_due_date': orders_missing_due_date,
            'orders_with_due_date': 0
        }

    # Calculate days late for each order (negative = early, positive = late)
    valid_df['Days_Late'] = (valid_df['Finished_Date'] - valid_df['Due_Date']).dt.days

    # Late = Finished > Due (Days_Late > 0)
    late_orders = valid_df[valid_df['Days_Late'] > 0]
    total_late_orders = len(late_orders)
    total_days_late = late_orders['Days_Late'].sum() if not late_orders.empty else 0
    avg_days_late = late_orders['Days_Late'].mean() if not late_orders.empty else 0.0

    on_time_count = orders_with_due_date - total_late_orders
    on_time_rate = (on_time_count / orders_with_due_date * 100)

    return {
        'on_time_rate': round(on_time_rate, 1),
        'total_late_orders': int(total_late_orders),
        'total_days_late': int(total_days_late),
        'avg_days_late': round(avg_days_late, 1),
        'orders_missing_due_date': int(orders_missing_due_date),
        'orders_with_due_date': int(orders_with_due_date)
    }


def get_recurring_problem_skus(
    xlsx,
    selected_months: List[str],
    all_monthly_sheets: List[str],
    lookback: int = 6,
    top_n: int = 5,
    min_appearances: int = 3
) -> pd.DataFrame:
    """
    Identify Parent SKUs appearing in top problem list for multiple months.

    Args:
        xlsx: Excel file object
        selected_months: Currently selected months
        all_monthly_sheets: All available monthly sheets
        lookback: Number of months to look back
        top_n: Top N problem SKUs per month to consider
        min_appearances: Minimum appearances to flag as recurring

    Returns:
        DataFrame with recurring problem SKUs
    """
    from .data_loader import get_lookback_months, load_ss_data_from_sheet

    if not selected_months:
        return pd.DataFrame()

    # Use the most recent selected month as reference
    sorted_selected = sorted(selected_months, key=lambda x: (int(x[3:]), x[:3]))
    current_month = sorted_selected[-1]

    # Get lookback window
    lookback_months = get_lookback_months(all_monthly_sheets, current_month, lookback)

    if not lookback_months:
        return pd.DataFrame()

    # Track appearances per Parent SKU
    sku_appearances = {}  # Parent_SKU -> list of months

    for month in lookback_months:
        try:
            month_df = load_ss_data_from_sheet(xlsx, month)
            if month_df.empty:
                continue

            month_df = add_parent_sku_column(month_df, 'SKU')

            # Aggregate by Parent SKU
            sku_stats = month_df.groupby('Parent_SKU').agg({
                'Quantity': 'sum',
                'Scrap': 'sum'
            }).reset_index()

            sku_stats['Fail_Rate'] = (sku_stats['Scrap'] / sku_stats['Quantity'] * 100)

            # Get top N by fail count (using Scrap as fail count)
            top_skus = sku_stats.nlargest(top_n, 'Scrap')['Parent_SKU'].tolist()

            for sku in top_skus:
                if sku not in sku_appearances:
                    sku_appearances[sku] = []
                sku_appearances[sku].append(month)

        except Exception:
            continue

    # Filter to SKUs appearing in min_appearances or more months
    recurring = []
    for sku, months in sku_appearances.items():
        if len(months) >= min_appearances:
            recurring.append({
                'Parent_SKU': sku,
                'Months_In_Top5': len(months),
                'Month_List': ', '.join(months)
            })

    if not recurring:
        return pd.DataFrame()

    result = pd.DataFrame(recurring)
    result = result.sort_values('Months_In_Top5', ascending=False)

    return result


def get_inspector_sku_concentration(
    df: pd.DataFrame,
    min_sku_volume: int = 10,
    threshold_pct: float = 50.0
) -> pd.DataFrame:
    """
    Identify inspectors with high concentration of a specific Parent SKU.

    Args:
        df: DataFrame with Inspector and Parent_SKU columns
        min_sku_volume: Minimum total orders for a SKU to be considered
        threshold_pct: Concentration percentage to flag (default 50%)

    Returns:
        DataFrame with concentration alerts
    """
    # Inspectors to exclude from concentration alerts:
    # - BRYCE: QC Manager, intentionally focuses on specific SKUs (BU items)
    # - PA/SEWING ASST: Handles different product types by design
    EXCLUDED_INSPECTORS = ['BRYCE', 'PA/SEWING ASST', 'PA/SEWING ASST.']

    df = add_parent_sku_column(df, 'SKU')

    # Get total orders per Parent SKU
    sku_totals = df.groupby('Parent_SKU')['Order_Number'].nunique().reset_index()
    sku_totals.columns = ['Parent_SKU', 'Total_SKU_Orders']

    # Filter to SKUs with sufficient volume
    valid_skus = sku_totals[sku_totals['Total_SKU_Orders'] >= min_sku_volume]['Parent_SKU'].tolist()

    if not valid_skus:
        return pd.DataFrame()

    # For each valid SKU, calculate inspector distribution
    alerts = []
    df_filtered = df[df['Parent_SKU'].isin(valid_skus)]

    for sku in valid_skus:
        sku_df = df_filtered[df_filtered['Parent_SKU'] == sku]
        total_orders = sku_df['Order_Number'].nunique()

        inspector_orders = sku_df.groupby('Inspector')['Order_Number'].nunique().reset_index()
        inspector_orders.columns = ['Inspector', 'Inspector_SKU_Orders']

        for _, row in inspector_orders.iterrows():
            # Skip excluded inspectors
            inspector_upper = row['Inspector'].upper().strip()
            if any(excl.upper() in inspector_upper for excl in EXCLUDED_INSPECTORS):
                continue

            concentration_pct = (row['Inspector_SKU_Orders'] / total_orders * 100)
            if concentration_pct > threshold_pct:
                alerts.append({
                    'Inspector': row['Inspector'],
                    'Parent_SKU': sku,
                    'Inspector_SKU_Orders': row['Inspector_SKU_Orders'],
                    'Total_SKU_Orders': total_orders,
                    'Concentration_Pct': round(concentration_pct, 1),
                    'Alert': True
                })

    if not alerts:
        return pd.DataFrame()

    result = pd.DataFrame(alerts)
    result = result.sort_values('Concentration_Pct', ascending=False)

    return result


def filter_active_inspectors(df: pd.DataFrame, selected_months: List[str]) -> List[str]:
    """
    Get inspectors present in the most recent selected month.

    Args:
        df: DataFrame with Inspector and Month columns
        selected_months: List of selected month sheet names

    Returns:
        List of active inspector names
    """
    if not selected_months or df.empty:
        return []

    # Sort months to find most recent
    from .data_loader import parse_month_string
    sorted_months = sorted(selected_months, key=parse_month_string)
    most_recent = sorted_months[-1]

    # Get unique inspectors from most recent month
    recent_df = df[df['Month'] == most_recent]
    active_inspectors = recent_df['Inspector'].unique().tolist()

    return active_inspectors


def get_monthly_trends_extended(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate extended monthly trend metrics including NCRs and touch rate.

    Args:
        df: DataFrame with SS stream data (must have 'Month' column)

    Returns:
        DataFrame with extended monthly metrics
    """
    # Define month order for sorting
    month_order = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
                   'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']

    monthly_stats = df.groupby('Month').agg({
        'Quantity': 'sum',
        'Final_Qty': 'sum',
        'Repairs': 'sum',
        'Scrap': 'sum',
        'QC_Fail': 'sum',
        'Sewing_Fail': 'sum',
        'Order_Number': 'nunique',
        'Red_Flag': lambda x: (x == 'X').sum(),
        'NCR_Complete': lambda x: (x == 'X').sum()
    }).reset_index()

    monthly_stats.columns = ['Month', 'Quantity', 'Final_Qty', 'Repairs', 'Scrap',
                              'QC_Fail', 'Sewing_Fail', 'Orders', 'Red_Flags', 'NCR_Count']

    # Calculate rates
    monthly_stats['Pass_Rate'] = (monthly_stats['Final_Qty'] / monthly_stats['Quantity'] * 100).round(2)
    monthly_stats['Fail_Rate'] = (monthly_stats['Scrap'] / monthly_stats['Quantity'] * 100).round(2)
    monthly_stats['Repair_Rate'] = (monthly_stats['Repairs'] / monthly_stats['Quantity'] * 100).round(2)
    monthly_stats['Total_Fails'] = monthly_stats['Scrap']
    monthly_stats['Total_Reworks'] = monthly_stats['Repairs']

    # Touch Rate = (Repairs + Scrap) / Quantity * 100
    monthly_stats['Touch_Rate'] = (
        (monthly_stats['Repairs'] + monthly_stats['Scrap']) / monthly_stats['Quantity'] * 100
    ).round(2)

    # Sort by month/year
    def month_sort_key(month_str):
        month = month_str[:3]
        year = int(month_str[3:])
        month_num = month_order.index(month) if month in month_order else 0
        return (year, month_num)

    monthly_stats['sort_key'] = monthly_stats['Month'].apply(month_sort_key)
    monthly_stats = monthly_stats.sort_values('sort_key').drop('sort_key', axis=1)

    return monthly_stats


def get_repairs_by_parent_sku(df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """
    Get repair metrics aggregated by Parent SKU.

    Args:
        df: DataFrame with SS stream data
        top_n: Number of top SKUs to return

    Returns:
        DataFrame with repair metrics by Parent SKU
    """
    df = add_parent_sku_column(df, 'SKU')

    sku_stats = df.groupby('Parent_SKU').agg({
        'Quantity': 'sum',
        'Repairs': 'sum',
        'Scrap': 'sum',
        'Sewing_Fail': 'sum',
        'QC_Fail': 'sum'
    }).reset_index()

    sku_stats['Repair_Rate'] = (sku_stats['Repairs'] / sku_stats['Quantity'] * 100).round(2)
    sku_stats['Fail_Rate'] = (sku_stats['Scrap'] / sku_stats['Quantity'] * 100).round(2)

    # Sort by repairs (descending)
    sku_stats = sku_stats.sort_values('Repairs', ascending=False)

    return sku_stats.head(top_n)
