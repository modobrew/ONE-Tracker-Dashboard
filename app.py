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
from utils.data_loader import (
    load_excel_file,
    load_all_ss_data,
    get_monthly_sheets,
    generate_month_presets,
    get_lookback_months
)
from utils.metrics import (
    calculate_summary_metrics,
    get_problem_skus,
    get_top_repair_skus,
    get_inspector_performance,
    get_monthly_trends,
    get_red_flag_analysis,
    generate_insights,
    calculate_on_time_metrics,
    get_recurring_problem_skus,
    get_inspector_sku_concentration,
    filter_active_inspectors,
    get_monthly_trends_extended,
    get_repairs_by_parent_sku,
    TARGET_ON_TIME_RATE
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

                # Generate presets
                presets = generate_month_presets(monthly_sheets)

                # Preset selector
                preset_options = ["Custom (Manual Selection)"] + list(presets.keys())
                selected_preset = st.selectbox(
                    "Quick Select",
                    options=preset_options,
                    index=0,
                    help="Choose a preset or select Custom for manual selection"
                )

                # Determine default months based on preset
                if selected_preset == "Custom (Manual Selection)":
                    default_months = monthly_sheets[-1:] if monthly_sheets else []
                else:
                    default_months = presets.get(selected_preset, [])
                    # Filter to only months that exist in the file
                    default_months = [m for m in default_months if m in monthly_sheets]

                selected_months = st.multiselect(
                    "Months to analyze",
                    options=monthly_sheets,
                    default=default_months,
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

    # New metrics
    on_time_metrics = calculate_on_time_metrics(df)
    recurring_skus = get_recurring_problem_skus(xlsx, selected_months, monthly_sheets)
    sku_concentration = get_inspector_sku_concentration(df)
    active_inspectors = filter_active_inspectors(df, selected_months)
    repairs_by_sku = get_repairs_by_parent_sku(df)
    monthly_trends_ext = get_monthly_trends_extended(df)

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
                                        top_repair_skus, inspector_perf, insights, on_time_metrics)
    elif role == "Operations Director":
        render_operations_director_view(df, metrics, problem_skus_by_count, insights,
                                         red_flag_analysis, monthly_trends_ext, sku_concentration)
    elif role == "QC Manager":
        render_qc_manager_view(df, metrics, inspector_perf, red_flag_analysis, insights,
                                sku_concentration, active_inspectors)
    elif role == "Sewing Manager":
        render_sewing_manager_view(df, metrics, problem_skus_by_count, insights,
                                    recurring_skus, repairs_by_sku)

    # Monthly trends (if multiple months selected)
    if len(selected_months) > 1:
        st.markdown("---")
        st.markdown("#### 📊 Monthly Trends")
        monthly_trends = get_monthly_trends(df)
        render_trend_charts(monthly_trends)


def render_production_manager_view(df, metrics, problem_by_count, problem_by_rate,
                                    top_repairs, inspector_perf, insights, on_time_metrics):
    """Render Production Manager dashboard view."""

    # On-Time Delivery Section
    st.markdown("#### 📦 On-Time Delivery")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        # Color based on target (97%)
        rate_color = "normal" if on_time_metrics['on_time_rate'] >= TARGET_ON_TIME_RATE else "inverse"
        st.metric(
            label="On-Time Rate",
            value=f"{on_time_metrics['on_time_rate']:.1f}%",
            delta=f"Target: {TARGET_ON_TIME_RATE}%" if on_time_metrics['on_time_rate'] >= TARGET_ON_TIME_RATE else f"Below {TARGET_ON_TIME_RATE}% target",
            delta_color=rate_color
        )

    with col2:
        st.metric(label="Late Orders", value=f"{on_time_metrics['total_late_orders']:,}")

    with col3:
        st.metric(label="Total Days Late", value=f"{on_time_metrics['total_days_late']:,}")

    with col4:
        st.metric(label="Avg Days Late", value=f"{on_time_metrics['avg_days_late']:.1f}")

    # Data quality warning
    if on_time_metrics['orders_missing_due_date'] > 0:
        st.warning(f"⚠️ {on_time_metrics['orders_missing_due_date']} orders excluded from on-time calculation (missing Due Date)")

    st.markdown("---")

    # Insights section
    st.markdown("#### 💡 Key Insights")

    # Add on-time insight
    if on_time_metrics['on_time_rate'] >= TARGET_ON_TIME_RATE:
        st.markdown(f"- ✅ On-time delivery at {on_time_metrics['on_time_rate']:.1f}% - meeting target")
    else:
        st.markdown(f"- 🔴 On-time delivery at {on_time_metrics['on_time_rate']:.1f}% - below {TARGET_ON_TIME_RATE}% target")

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


def render_operations_director_view(df, metrics, problem_by_count, insights, red_flags,
                                      monthly_trends_ext, sku_concentration):
    """Render Operations Director dashboard view."""

    # High-level insights
    st.markdown("#### 💡 Executive Summary")

    # Touch rate insight
    if not monthly_trends_ext.empty:
        avg_touch_rate = monthly_trends_ext['Touch_Rate'].mean()
        st.markdown(f"- 📈 Average touch rate is {avg_touch_rate:.1f}% (repairs + scrap) - proxy for COPQ labor drag")

    for insight in insights:
        st.markdown(f"- {insight}")

    st.markdown("---")

    # Month-over-Month Trends (if multiple months)
    if len(monthly_trends_ext) > 1:
        st.markdown("#### 📊 Month-over-Month Trends")
        col1, col2 = st.columns(2)

        with col1:
            # NCRs trend
            fig = px.line(monthly_trends_ext, x='Month', y='NCR_Count',
                          markers=True, title='NCRs by Month')
            fig.update_layout(height=300, yaxis_title='NCR Count', xaxis_title='Month')
            fig.update_traces(line_color='#dc3545')
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Fails and Reworks trend
            fig = go.Figure()
            fig.add_trace(go.Bar(x=monthly_trends_ext['Month'], y=monthly_trends_ext['Total_Fails'],
                                  name='Total Fails', marker_color='#dc3545'))
            fig.add_trace(go.Bar(x=monthly_trends_ext['Month'], y=monthly_trends_ext['Total_Reworks'],
                                  name='Reworks', marker_color='#ffc107'))
            fig.update_layout(barmode='group', title='Fails & Reworks by Month',
                              height=300, yaxis_title='Count', xaxis_title='Month')
            st.plotly_chart(fig, use_container_width=True)

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

    # Only show inspector concentration if there are alerts
    if not sku_concentration.empty:
        st.markdown("---")
        st.markdown("#### 👥 Inspector SKU Concentration Alerts")
        st.info("Flagged inspectors have >50% of a Parent SKU's volume (potential workload imbalance)")
        display_df = sku_concentration[['Inspector', 'Parent_SKU', 'Concentration_Pct',
                                         'Inspector_SKU_Orders', 'Total_SKU_Orders']].copy()
        display_df.columns = ['Inspector', 'Parent SKU', 'Concentration %',
                              'Inspector Orders', 'Total SKU Orders']
        st.dataframe(display_df, use_container_width=True, hide_index=True)


def render_qc_manager_view(df, metrics, inspector_perf, red_flags, insights,
                            sku_concentration, active_inspectors):
    """Render QC Manager dashboard view."""

    st.markdown("#### 💡 Key Insights")
    for insight in insights:
        st.markdown(f"- {insight}")

    # SKU Concentration Alerts
    if not sku_concentration.empty:
        st.markdown("---")
        st.markdown("#### ⚠️ SKU Distribution Alerts")
        st.warning("The following inspectors have >50% of a Parent SKU's volume:")
        display_df = sku_concentration[['Inspector', 'Parent_SKU', 'Concentration_Pct',
                                         'Inspector_SKU_Orders', 'Total_SKU_Orders']].copy()
        display_df.columns = ['Inspector', 'Parent SKU', 'Concentration %',
                              'Inspector Orders', 'Total SKU Orders']
        st.dataframe(display_df, use_container_width=True, hide_index=True)

    st.markdown("---")

    # Separate PA/SEWING ASST from comparison
    if not inspector_perf.empty:
        # Identify PA/SEWING ASST entries
        pa_mask = inspector_perf['Inspector'].str.contains('PA/SEWING', case=False, na=False)
        pa_data = inspector_perf[pa_mask].copy()
        comparison_data = inspector_perf[~pa_mask].copy()

        # Filter to active inspectors only (exclude former employees)
        if active_inspectors:
            comparison_data = comparison_data[comparison_data['Inspector'].isin(active_inspectors)]

        # Inspector performance comparison
        st.markdown("#### 👥 Inspector Performance Comparison")
        st.caption("Excludes PA/SEWING ASST (handles different work type) and former employees")

        if not comparison_data.empty:
            display_df = comparison_data[[
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
                comparison_data,
                x='Inspector',
                y='Quantity',
                color='Pass_Rate',
                color_continuous_scale='RdYlGn',
                labels={'Quantity': 'Products Inspected', 'Pass_Rate': 'Pass Rate %'}
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No inspector comparison data available")

        # Show PA/SEWING ASST volume separately
        if not pa_data.empty:
            st.markdown("---")
            st.markdown("#### 📦 PA/SEWING ASST Volume (Reference Only)")
            st.caption("Handles simpler packaging work - not included in performance comparison")
            pa_display = pa_data[['Inspector', 'Quantity', 'Repairs']].copy()
            pa_display.columns = ['Role', 'Qty Inspected', 'Repairs']
            st.dataframe(pa_display, use_container_width=True, hide_index=True)

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


def render_sewing_manager_view(df, metrics, problem_by_count, insights,
                                recurring_skus, repairs_by_sku):
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
            help="% of defects caught at sewing (higher = better early detection)"
        )

    st.markdown("---")

    # Insights
    st.markdown("#### 💡 Key Insights")
    sewing_insights = [i for i in insights if 'sewing' in i.lower() or 'detection' in i.lower()]
    for insight in sewing_insights if sewing_insights else insights[:3]:
        st.markdown(f"- {insight}")

    st.markdown("---")

    # Recurring Problem SKUs (6-month analysis)
    st.markdown("#### 🔄 Recurring Problem SKUs (6-Month Analysis)")
    st.caption("Parent SKUs appearing in top 5 problem list for 3+ of the last 6 months")

    if not recurring_skus.empty:
        display_df = recurring_skus[['Parent_SKU', 'Months_In_Top5', 'Month_List']].copy()
        display_df.columns = ['Parent SKU', 'Months in Top 5', 'Months']
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        st.info("These SKUs may need: operator retraining, updated work instructions, or R&D design review")
    else:
        st.success("No recurring problem SKUs detected in the last 6 months!")

    st.markdown("---")

    # Two-column layout for sewing issues and repairs
    col1, col2 = st.columns(2)

    with col1:
        # SKUs with sewing issues
        st.markdown("#### 🔴 Top SKUs by Sewing Fails")
        df_with_parent = add_parent_sku_column(df, 'SKU')

        sewing_issues = df_with_parent.groupby('Parent_SKU').agg({
            'Quantity': 'sum',
            'Sewing_Fail': 'sum',
            'QC_Fail': 'sum'
        }).reset_index()

        sewing_issues['Sewing_Fail_Rate'] = (sewing_issues['Sewing_Fail'] / sewing_issues['Quantity'] * 100).round(2)
        sewing_issues = sewing_issues[sewing_issues['Sewing_Fail'] > 0].sort_values('Sewing_Fail', ascending=False)

        if not sewing_issues.empty:
            display_df = sewing_issues.head(10)[['Parent_SKU', 'Quantity', 'Sewing_Fail', 'Sewing_Fail_Rate']].copy()
            display_df.columns = ['Parent SKU', 'Qty Inspected', 'Sewing Fails', 'Sewing Fail Rate %']
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.success("No sewing fails recorded!")

    with col2:
        # Repairs by Parent SKU
        st.markdown("#### 🔧 Top SKUs by Repairs")
        st.caption("Repairs = sewing team rework (unplanned downtime)")

        if not repairs_by_sku.empty:
            display_df = repairs_by_sku[['Parent_SKU', 'Quantity', 'Repairs', 'Repair_Rate']].copy()
            display_df.columns = ['Parent SKU', 'Qty Inspected', 'Repairs', 'Repair Rate %']
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("No repair data available")


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
