"""
ONE Tracker Dashboard
A Streamlit web application for analyzing QC production data.

Usage:
    streamlit run app.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.data_loader import load_excel_file, load_all_ss_data, get_monthly_sheets
from utils.metrics import (
    calculate_summary_metrics,
    get_problem_skus,
    get_top_repair_skus,
    get_inspector_performance,
    get_monthly_trends,
    get_red_flag_analysis,
    generate_insights
)
from utils.sku_utils import add_parent_sku_column

# Page configuration
st.set_page_config(
    page_title="ONE Tracker Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
    }
    .stMetric {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .insight-box {
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
        background-color: #f8f9fa;
    }
</style>
""", unsafe_allow_html=True)


def main():
    # Header
    st.title("📊 ONE Tracker Dashboard")
    st.markdown("*QC Production Analysis Tool*")

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")

        # Role selector
        role = st.selectbox(
            "Select Role View",
            ["Production Manager", "Operations Director", "QC Manager", "Sewing Manager"],
            index=0
        )

        st.markdown("---")

        # File uploader
        st.subheader("📁 Upload Data")
        uploaded_file = st.file_uploader(
            "Upload ONE Tracker Excel file",
            type=['xlsx', 'xls'],
            help="Upload the ONE Tracker Excel file to analyze"
        )

        # Month selector (will populate after file upload)
        selected_months = None

    # Main content area
    if uploaded_file is None:
        # Show instructions when no file is uploaded
        st.info("👈 Upload your ONE Tracker Excel file in the sidebar to get started.")

        st.markdown("""
        ### Welcome to the ONE Tracker Dashboard

        This tool helps you analyze QC production data with:

        - **Summary Metrics**: Pass rate, fail rate, repair rate, scrap rate
        - **Problem SKU Analysis**: Top SKUs by fail count and fail rate
        - **Inspector Performance**: Track individual QC inspector metrics
        - **Trend Analysis**: Month-over-month quality trends
        - **Automated Insights**: Key observations and alerts

        #### Getting Started
        1. Upload your ONE Tracker Excel file using the sidebar
        2. Select which months to analyze
        3. Choose your role view for relevant metrics
        4. Explore the dashboard!
        """)
        return

    # Load the data
    try:
        with st.spinner("Loading data..."):
            xlsx, monthly_sheets = load_excel_file(uploaded_file)

            # Month selector in sidebar
            with st.sidebar:
                st.subheader("📅 Select Months")
                selected_months = st.multiselect(
                    "Months to analyze",
                    options=monthly_sheets,
                    default=monthly_sheets[-1:] if monthly_sheets else [],  # Default to most recent
                    help="Select one or more months to include in analysis"
                )

                if not selected_months:
                    st.warning("Please select at least one month")
                    return

            # Load SS data for selected months
            df = load_all_ss_data(xlsx, selected_months)

            if df.empty:
                st.error("No data found for selected months.")
                return

    except Exception as e:
        st.error(f"Error loading file: {str(e)}")
        return

    # Calculate metrics
    metrics = calculate_summary_metrics(df)
    problem_skus_by_count, problem_skus_by_rate = get_problem_skus(df)
    top_repair_skus = get_top_repair_skus(df)
    inspector_perf = get_inspector_performance(df)
    red_flag_analysis = get_red_flag_analysis(df)
    insights = generate_insights(metrics, (problem_skus_by_count, problem_skus_by_rate), inspector_perf)

    # Display based on role
    st.markdown(f"### 📋 {role} View")
    st.caption(f"Analyzing: {', '.join(selected_months)} | SS Stream Only")

    # Summary Cards (all roles see these)
    st.markdown("#### 📈 Summary Metrics")
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            label="Pass Rate",
            value=f"{metrics['pass_rate']:.1f}%",
            delta=None
        )

    with col2:
        st.metric(
            label="Fail Rate",
            value=f"{metrics['fail_rate']:.1f}%",
            delta=None
        )

    with col3:
        st.metric(
            label="Repair Rate",
            value=f"{metrics['repair_rate']:.1f}%",
            delta=None
        )

    with col4:
        st.metric(
            label="Scrap Rate",
            value=f"{metrics['scrap_rate']:.1f}%",
            delta=None
        )

    with col5:
        st.metric(
            label="Total Inspected",
            value=f"{metrics['total_inspected']:,}"
        )

    # Second row of metrics
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(label="Total Orders", value=f"{metrics['total_orders']:,}")

    with col2:
        st.metric(label="Total Fails", value=f"{metrics['total_fails']:,}")

    with col3:
        st.metric(label="Total Repairs", value=f"{metrics['total_repairs']:,}")

    with col4:
        st.metric(label="Total Scrap", value=f"{metrics['total_scrap']:,}")

    with col5:
        st.metric(label="Red Flags", value=f"{metrics['total_red_flags']}")

    st.markdown("---")

    # Role-specific content
    if role == "Production Manager":
        render_production_manager_view(df, metrics, problem_skus_by_count, problem_skus_by_rate,
                                        top_repair_skus, inspector_perf, insights)
    elif role == "Operations Director":
        render_operations_director_view(df, metrics, problem_skus_by_count, insights, red_flag_analysis)
    elif role == "QC Manager":
        render_qc_manager_view(df, metrics, inspector_perf, red_flag_analysis, insights)
    elif role == "Sewing Manager":
        render_sewing_manager_view(df, metrics, problem_skus_by_count, insights)

    # Monthly trends (if multiple months selected)
    if len(selected_months) > 1:
        st.markdown("---")
        st.markdown("#### 📊 Monthly Trends")
        monthly_trends = get_monthly_trends(df)
        render_trend_charts(monthly_trends)


def render_production_manager_view(df, metrics, problem_by_count, problem_by_rate,
                                    top_repairs, inspector_perf, insights):
    """Render Production Manager dashboard view."""

    # Insights section
    st.markdown("#### 💡 Key Insights")
    for insight in insights:
        st.markdown(f"- {insight}")

    st.markdown("---")

    # Two columns for problem SKUs
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🔴 Top Problem SKUs (by Fail Count)")
        if not problem_by_count.empty:
            display_df = problem_by_count[['Parent_SKU', 'Quantity', 'Total_Fails', 'Fail_Rate']].copy()
            display_df.columns = ['Parent SKU', 'Qty Inspected', 'Total Fails', 'Fail Rate %']
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("No data available")

    with col2:
        st.markdown("#### 📊 Top Problem SKUs (by Fail Rate)")
        st.caption("Minimum 10 units inspected")
        if not problem_by_rate.empty:
            display_df = problem_by_rate[['Parent_SKU', 'Quantity', 'Total_Fails', 'Fail_Rate']].copy()
            display_df.columns = ['Parent SKU', 'Qty Inspected', 'Total Fails', 'Fail Rate %']
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("No data available")

    st.markdown("---")

    # Repairs and Inspector sections
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🔧 Top SKUs by Repairs")
        if not top_repairs.empty:
            display_df = top_repairs[['Parent_SKU', 'Quantity', 'Repairs', 'Repair_Rate']].copy()
            display_df.columns = ['Parent SKU', 'Qty Inspected', 'Repairs', 'Repair Rate %']
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("No data available")

    with col2:
        st.markdown("#### 👤 Inspector Summary")
        if not inspector_perf.empty:
            display_df = inspector_perf[['Inspector', 'Quantity', 'Pass_Rate', 'Total_Fails']].copy()
            display_df.columns = ['Inspector', 'Qty Inspected', 'Pass Rate %', 'Total Fails']
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("No data available")


def render_operations_director_view(df, metrics, problem_by_count, insights, red_flags):
    """Render Operations Director dashboard view."""

    # High-level insights
    st.markdown("#### 💡 Executive Summary")
    for insight in insights:
        st.markdown(f"- {insight}")

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        # Quality pie chart
        st.markdown("#### 📊 Quality Distribution")
        fig = go.Figure(data=[go.Pie(
            labels=['Passed', 'Scrapped'],
            values=[metrics['total_passed'], metrics['total_scrap']],
            hole=.4,
            marker_colors=['#28a745', '#dc3545']
        )])
        fig.update_layout(height=300, margin=dict(t=20, b=20, l=20, r=20))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Red flags analysis
        st.markdown("#### 🚩 Customer Returns (Red Flags)")
        if not red_flags.empty:
            st.dataframe(red_flags.head(10), use_container_width=True, hide_index=True)
        else:
            st.success("No customer returns this period!")

    st.markdown("---")

    # Problem SKUs for executive review
    st.markdown("#### ⚠️ SKUs Requiring Attention")
    if not problem_by_count.empty:
        display_df = problem_by_count[['Parent_SKU', 'Quantity', 'Total_Fails', 'Fail_Rate', 'Repairs']].copy()
        display_df.columns = ['Parent SKU', 'Volume', 'Fails', 'Fail Rate %', 'Repairs']
        st.dataframe(display_df, use_container_width=True, hide_index=True)


def render_qc_manager_view(df, metrics, inspector_perf, red_flags, insights):
    """Render QC Manager dashboard view."""

    st.markdown("#### 💡 Key Insights")
    for insight in insights:
        st.markdown(f"- {insight}")

    st.markdown("---")

    # Inspector performance details
    st.markdown("#### 👥 Inspector Performance Details")
    if not inspector_perf.empty:
        display_df = inspector_perf[[
            'Inspector', 'Quantity', 'Pass_Rate', 'Total_Fails',
            'QC_Fail', 'Sewing_Fail', 'Repairs', 'Red_Flags'
        ]].copy()
        display_df.columns = [
            'Inspector', 'Qty Inspected', 'Pass Rate %', 'Total Fails',
            'QC Fails', 'Sewing Fails', 'Repairs', 'Red Flags'
        ]
        st.dataframe(display_df, use_container_width=True, hide_index=True)

        # Inspector comparison chart
        st.markdown("#### 📊 Inspector Volume Comparison")
        fig = px.bar(
            inspector_perf,
            x='Inspector',
            y='Quantity',
            color='Pass_Rate',
            color_continuous_scale='RdYlGn',
            labels={'Quantity': 'Products Inspected', 'Pass_Rate': 'Pass Rate %'}
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # NCR / Red Flag tracking
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🚩 Red Flag Orders (NCR Review)")
        red_flag_orders = df[df['Red_Flag'] == 'X'][['Order_Number', 'SKU', 'Inspector', 'Quantity', 'NCR_Complete']].copy()
        if not red_flag_orders.empty:
            red_flag_orders.columns = ['Order', 'SKU', 'Inspector', 'Qty', 'NCR Done']
            st.dataframe(red_flag_orders, use_container_width=True, hide_index=True)
        else:
            st.success("No red flags this period!")

    with col2:
        st.markdown("#### 📈 Defect Detection")
        st.metric(
            label="Sewing Detection Rate",
            value=f"{metrics['sewing_detection_rate']:.1f}%",
            help="Percentage of defects caught at sewing vs QC"
        )
        st.caption("Higher is better - defects caught earlier save time")


def render_sewing_manager_view(df, metrics, problem_by_count, insights):
    """Render Sewing Manager dashboard view."""

    # Sewing-specific metrics
    st.markdown("#### 🧵 Sewing Quality Metrics")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="Sewing Fails",
            value=f"{metrics['total_sewing_fails']:,}"
        )

    with col2:
        st.metric(
            label="QC Fails (escaped sewing)",
            value=f"{metrics['total_qc_fails']:,}"
        )

    with col3:
        st.metric(
            label="Sewing Detection Rate",
            value=f"{metrics['sewing_detection_rate']:.1f}%",
            help="% of defects caught at sewing"
        )

    st.markdown("---")

    # Insights
    st.markdown("#### 💡 Key Insights")
    sewing_insights = [i for i in insights if 'sewing' in i.lower() or 'detection' in i.lower()]
    for insight in sewing_insights if sewing_insights else insights[:3]:
        st.markdown(f"- {insight}")

    st.markdown("---")

    # SKUs with sewing issues
    st.markdown("#### 🔴 SKUs with Sewing Issues")
    df_with_parent = add_parent_sku_column(df, 'SKU')

    sewing_issues = df_with_parent.groupby('Parent_SKU').agg({
        'Quantity': 'sum',
        'Sewing_Fail': 'sum',
        'QC_Fail': 'sum'
    }).reset_index()

    sewing_issues['Sewing_Fail_Rate'] = (sewing_issues['Sewing_Fail'] / sewing_issues['Quantity'] * 100).round(2)
    sewing_issues = sewing_issues[sewing_issues['Sewing_Fail'] > 0].sort_values('Sewing_Fail', ascending=False)

    if not sewing_issues.empty:
        display_df = sewing_issues.head(10)[['Parent_SKU', 'Quantity', 'Sewing_Fail', 'Sewing_Fail_Rate', 'QC_Fail']].copy()
        display_df.columns = ['Parent SKU', 'Qty Inspected', 'Sewing Fails', 'Sewing Fail Rate %', 'QC Fails (escaped)']
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        st.success("No sewing fails recorded!")


def render_trend_charts(monthly_df):
    """Render monthly trend charts."""

    col1, col2 = st.columns(2)

    with col1:
        # Pass rate trend
        fig = px.line(
            monthly_df,
            x='Month',
            y='Pass_Rate',
            markers=True,
            title='Pass Rate Trend'
        )
        fig.update_layout(yaxis_title='Pass Rate %', xaxis_title='Month')
        fig.update_traces(line_color='#28a745')
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Volume trend
        fig = px.bar(
            monthly_df,
            x='Month',
            y='Quantity',
            title='Inspection Volume Trend'
        )
        fig.update_layout(yaxis_title='Products Inspected', xaxis_title='Month')
        st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    main()
