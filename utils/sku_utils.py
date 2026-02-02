"""
SKU Utility Functions for ONE Tracker Dashboard
Handles parent SKU rollup logic
"""

import pandas as pd

# Complete list of color codes - ONLY these codes, no others
# Note: CR is NOT a color code - it's a product line prefix
COLOR_CODES = {
    'BK', 'CB', 'MC', 'MA', 'MB', 'MT', 'RG', 'WD', 'WG',
    'TB', 'TD', 'TJ', 'RD', 'ML', 'NG', 'NP', 'RT'
}

# SKUs where apparent color codes are actually part of the product name
EXCEPTIONS = {'PI-CB', 'MI-556-TR', 'MI-556-SN'}


def get_parent_sku(sku: str) -> str:
    """
    Convert a full SKU to its parent SKU by removing color codes.

    Rules:
    1. Remove COLOR code only
    2. Keep SIZE designation if present
    3. Leave exceptions unchanged

    Examples:
        AC-ESE-BK -> AC-ESE (remove color)
        PC-F20-BK-LG -> PC-F20-LG (remove color, keep size)
        PI-CB -> PI-CB (exception)
        AC-HK -> AC-HK (no color code)

    Args:
        sku: The full SKU string

    Returns:
        The parent SKU with color codes removed
    """
    if pd.isna(sku):
        return sku

    sku = str(sku).strip()

    # Check exceptions first
    if sku in EXCEPTIONS:
        return sku

    # Split SKU into parts
    parts = sku.split('-')

    # Filter out color codes
    result = [p for p in parts if p not in COLOR_CODES]

    return '-'.join(result)


def add_parent_sku_column(df: pd.DataFrame, sku_column: str = 'SKU') -> pd.DataFrame:
    """
    Add a Parent_SKU column to a DataFrame.

    Args:
        df: DataFrame containing SKU data
        sku_column: Name of the column containing SKUs

    Returns:
        DataFrame with new Parent_SKU column
    """
    df = df.copy()
    df['Parent_SKU'] = df[sku_column].apply(get_parent_sku)
    return df


def get_color_from_sku(sku: str) -> str:
    """
    Extract the color code from a SKU.

    Args:
        sku: The full SKU string

    Returns:
        The color code if found, otherwise None
    """
    if pd.isna(sku):
        return None

    sku = str(sku).strip()

    if sku in EXCEPTIONS:
        return None

    parts = sku.split('-')

    for part in parts:
        if part in COLOR_CODES:
            return part

    return None
