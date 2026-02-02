"""
Data Loading Utilities for ONE Tracker Dashboard
Handles Excel parsing and data extraction
"""

import pandas as pd
from typing import Dict, List, Optional, Tuple


# Column mapping for SS table (columns 0-17)
SS_COLUMNS = {
    0: 'Order_Number',
    1: 'Lot_Number',
    2: 'Due_Date',
    3: 'Finished_Date',
    4: 'SKU',
    5: 'Quantity',
    6: 'Repairs',
    7: 'Repair_Pct',
    8: 'Scrap',
    9: 'Pass_Pct',
    10: 'Final_Qty',
    11: 'Inspector',
    12: 'Red_Flag',
    13: 'NCR_Complete',
    14: 'QC_Fail',
    15: 'Sewing_Fail',
    16: 'Stream',
    17: 'Notes'
}


def get_monthly_sheets(xlsx: pd.ExcelFile) -> List[str]:
    """
    Get list of monthly data sheets (e.g., JAN25, FEB25, etc.)
    Excludes Reference Lists and KPI sheets.

    Args:
        xlsx: Loaded Excel file object

    Returns:
        List of sheet names for monthly data
    """
    monthly_sheets = []
    for sheet in xlsx.sheet_names:
        # Skip non-data sheets
        if 'Reference' in sheet or 'KPI' in sheet:
            continue
        # Check if it matches MMMYY pattern (3 letters + 2 digits)
        if len(sheet) == 5 and sheet[:3].isalpha() and sheet[3:].isdigit():
            monthly_sheets.append(sheet)
    return monthly_sheets


def load_ss_data_from_sheet(xlsx: pd.ExcelFile, sheet_name: str) -> pd.DataFrame:
    """
    Load SS (in-house) stream data from a monthly sheet.

    Args:
        xlsx: Loaded Excel file object
        sheet_name: Name of the monthly sheet (e.g., 'JAN26')

    Returns:
        DataFrame with SS stream data, cleaned and typed
    """
    # Read raw data without headers
    df_raw = pd.read_excel(xlsx, sheet_name=sheet_name, header=None)

    # Extract SS columns (0-17)
    df_ss = df_raw.iloc[:, 0:18].copy()

    # Rename columns
    df_ss.columns = [SS_COLUMNS.get(i, f'Col_{i}') for i in range(18)]

    # Remove header row
    df_ss = df_ss.iloc[1:].reset_index(drop=True)

    # Filter out empty rows (where Order_Number is empty)
    df_ss = df_ss[df_ss['Order_Number'].notna() & (df_ss['Order_Number'] != '')]

    # Add month column for tracking
    df_ss['Month'] = sheet_name

    # Convert numeric columns
    numeric_cols = ['Quantity', 'Repairs', 'Scrap', 'Final_Qty', 'QC_Fail', 'Sewing_Fail']
    for col in numeric_cols:
        df_ss[col] = pd.to_numeric(df_ss[col], errors='coerce').fillna(0).astype(int)

    # Convert percentage columns
    pct_cols = ['Repair_Pct', 'Pass_Pct']
    for col in pct_cols:
        df_ss[col] = pd.to_numeric(df_ss[col], errors='coerce')

    # Convert date columns
    date_cols = ['Due_Date', 'Finished_Date']
    for col in date_cols:
        df_ss[col] = pd.to_datetime(df_ss[col], errors='coerce')

    # Clean text columns
    text_cols = ['Order_Number', 'Lot_Number', 'SKU', 'Inspector', 'Stream', 'Notes']
    for col in text_cols:
        df_ss[col] = df_ss[col].astype(str).str.strip()
        df_ss.loc[df_ss[col] == 'nan', col] = ''

    # Clean flag columns (X or empty)
    flag_cols = ['Red_Flag', 'NCR_Complete']
    for col in flag_cols:
        df_ss[col] = df_ss[col].astype(str).str.strip().str.upper()
        df_ss[col] = df_ss[col].apply(lambda x: 'X' if x == 'X' else '')

    return df_ss


def load_all_ss_data(xlsx: pd.ExcelFile, sheets: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Load SS data from multiple monthly sheets.

    Args:
        xlsx: Loaded Excel file object
        sheets: List of sheet names to load. If None, loads all monthly sheets.

    Returns:
        Combined DataFrame with SS data from all specified sheets
    """
    if sheets is None:
        sheets = get_monthly_sheets(xlsx)

    all_data = []
    for sheet in sheets:
        try:
            df = load_ss_data_from_sheet(xlsx, sheet)
            all_data.append(df)
        except Exception as e:
            print(f"Error loading sheet {sheet}: {e}")
            continue

    if not all_data:
        return pd.DataFrame()

    return pd.concat(all_data, ignore_index=True)


def load_excel_file(file) -> Tuple[pd.ExcelFile, List[str]]:
    """
    Load an Excel file and return the ExcelFile object and list of monthly sheets.

    Args:
        file: File path or file-like object (from Streamlit uploader)

    Returns:
        Tuple of (ExcelFile object, list of monthly sheet names)
    """
    xlsx = pd.ExcelFile(file)
    monthly_sheets = get_monthly_sheets(xlsx)
    return xlsx, monthly_sheets
