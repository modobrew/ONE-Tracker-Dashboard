"""
Metrics Calculation Utilities for ONE Tracker Dashboard
Handles KPI calculations and aggregations
"""

import pandas as pd
from typing import Dict, List, Optional, Tuple
from .sku_utils import add_parent_sku_column


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
