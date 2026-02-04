# ONE Tracker Reference Guide

---

## QUICK START - Resume Session

**Read this section first when resuming work on this project.**

### Project Location
```
/Users/modobrew/Documents/Claude-Projects-2026/ONE_Tracker/
```

### Live App (Streamlit Cloud)
**URL:** https://one-tracker-dashboard.streamlit.app

**GitHub Repo:** https://github.com/modobrew/ONE-Tracker-Dashboard

Share this URL with teammates - they can upload their own ONE Tracker files.

### To Run Locally
```bash
cd /Users/modobrew/Documents/Claude-Projects-2026/ONE_Tracker
streamlit run app.py
```
Then open browser to: http://localhost:8501

### To Stop Local Dashboard
Press `Ctrl+C` in the terminal, or:
```bash
pkill -f "streamlit run"
```

### To Update the Deployed App
Make changes locally, then:
```bash
git add .
git commit -m "Description of changes"
git push
```
Streamlit Cloud auto-redeploys on push.

### Current Project Status: ENHANCED & DEPLOYED (Feb 2026)
- Streamlit dashboard is live and functional
- Deployed to Streamlit Community Cloud
- All 4 role views enhanced with role-specific features:
  - **Production Manager**: On-time delivery metrics, problem SKUs, insights
  - **Operations Director**: MoM trend charts, SKU concentration alerts (conditional)
  - **QC Manager**: Inspector comparisons (PA/SEWING ASST separated), concentration alerts
  - **Sewing Manager**: Recurring problem SKUs (6-month), repairs by SKU
- Month presets (Q1-Q4 2025/2026, YTD) in sidebar
- Parent SKU rollup logic implemented and tested
- GitHub repo connected for easy updates (push to deploy)

### Key Files
| File | Purpose |
|------|---------|
| `app.py` | Main Streamlit dashboard application |
| `utils/data_loader.py` | Excel parsing, SS stream extraction |
| `utils/sku_utils.py` | Parent SKU rollup logic (color code removal) |
| `utils/metrics.py` | KPI calculations (pass rate, fail rate, etc.) |
| `requirements.txt` | Python dependencies |
| `.gitignore` | Git ignore rules (excludes .xlsx data files) |
| `ONE_Tracker_Reference.md` | This file - project documentation |
| `Roles.md` | Role-based output spec (KPIs, tables, insights per role) |
| `ONE_Tracker_JAN26.xlsx` | Sample data file (local only, not in repo) |

### Important Business Rules (Hardcoded)

**Color Codes - ONLY these 17, no others:**
```
BK, CB, MC, MA, MB, MT, RG, WD, WG, TB, TD, TJ, RD, ML, NG, NP, RT
```

**SKU Exceptions (do NOT modify):**
- `PI-CB` - CB is part of product name, not a color
- `MI-556-TR` - TR is not a color code
- `MI-556-SN` - SN is not a color code

**CR is a product prefix, NOT a color code** (e.g., CR-AL-BK, CR-FS-04)

**Total Fails = Scrap** (if something fails, it gets scrapped)
- QC_Fail and Sewing_Fail track WHERE the fail was caught, not additional fails

### Issues Fixed During Development
1. **CR prefix bug** - CR was incorrectly in color codes list, causing CR-AL to become just AL
2. **Total Fails calculation** - Changed from QC_Fail + Sewing_Fail to just Scrap
3. **False color codes removed** - Removed TN, GR, NV, BL, GY, WT (were never valid)
4. **Added TB** - Was missing from color codes

### Recently Completed (Feb 2026)
- ✅ On-time delivery metrics (Due Date vs Finished) for Production Manager
- ✅ Recurring problem SKU detection (6-month lookback) for Sewing Manager
- ✅ Inspector SKU distribution alerts (>50% concentration) for QC Manager
- ✅ Month-over-month trends (NCRs, fails, reworks) for Operations Director
- ✅ Repairs by Parent SKU for Sewing Manager
- ✅ Month presets (Q1-Q4 2025/2026, YTD)
- ✅ PA/SEWING ASST separated from inspector comparisons
- ✅ Former employee filtering

### Future Enhancements
- Export functionality (PDF/Excel reports)
- Date range filtering within months
- Drill-down into specific SKUs
- Email alerts for threshold breaches
- Cost of quality analysis (requires separate cost data)
- Sewing operator cross-reference (requires additional data source)

---

## Overview

The ONE Tracker is a QC Department tool used to track production orders completed through Quality Control. It monitors finished good SKUs, defects (sewing fails, QC fails), total output, scrap, and inspector performance.

**Primary Focus: SS Stream ONLY** (In-house production) - Dashboard excludes Bearse and Resale streams.

---

## File Structure

### Sheets

| Sheet Type | Examples | Purpose |
|------------|----------|---------|
| Monthly Data | JAN25, FEB25, ... DEC25, JAN26 | Raw QC inspection data by month |
| Monthly KPIs | 2025 Monthly KPIs, 2026 Monthly KPIs | Aggregated metrics by quarter/month |
| Reference Lists | Reference Lists | Data validation dropdowns (ignore for analysis) |

### Sheet Naming Convention
- Format: `MMMYY` (e.g., JAN25 = January 2025, JAN26 = January 2026)

---

## Monthly Sheet Structure

Each monthly sheet contains **3 side-by-side tables**, identified by the `Stream` column:

| Stream | Description | Column Range | Unique Fields |
|--------|-------------|--------------|---------------|
| **SS** | In-house produced products | Columns 0-17 | Has `Sewing Fail` column |
| **Bearse** | Subcontractor produced products | Columns 21-37 | No `Sewing Fail` column |
| **Resale** | Resale items (non-manufactured) | Columns 41-57 | No `Sewing Fail` column |

---

## Data Dictionary

### SS Table (In-House Production) - Columns 0-17

| Column | Field Name | Data Type | Description |
|--------|------------|-----------|-------------|
| 0 | Order Number | Text | Production order ID (e.g., PR20390) |
| 1 | Lot Number | Text | Lot identifier |
| 2 | Due Date | Date | Order due date |
| 3 | Finished | Date | Date QC inspection completed |
| 4 | Source No. (SKU) | Text | Product SKU identifier |
| 5 | Quantity | Integer | Initial quantity received for inspection |
| 6 | Repairs | Integer | Count of items repaired and passed |
| 7 | Repair % | Percentage | Repairs / Quantity |
| 8 | Scrap | Integer | Count of items that couldn't be salvaged |
| 9 | Pass % | Percentage | Pass rate after QC |
| 10 | Final Qty | Integer | Final passed quantity (= Quantity - Scrap) |
| 11 | Inspector | Text | QC Inspector name |
| 12 | Red Flag | Text | "X" if customer return due to defect |
| 13 | NCR Complete | Text | "X" when Non-Conformance Report issued |
| 14 | QC Fail | Integer | Count of fails caught at QC inspection |
| 15 | Sewing Fail | Integer | Count of fails caught during sewing |
| 16 | Stream | Text | Always "SS" |
| 17 | Notes | Text | Reason for repair, extras, missing items |

### Bearse Table (Subcontractor) - Columns 21-37

Same structure as SS table **except**:
- No `Sewing Fail` column (sewing done externally)
- Stream = "Bearse"

### Resale Table - Columns 41-57

Same structure as Bearse table:
- No `Sewing Fail` column (not manufactured)
- Stream = "Resale"

---

## Key Fields Explained

### Red Flag
- **Purpose**: Tracks customer returns due to defects
- **Entry**: Manually marked with "X" when a returned product is identified
- **Usage**: Links back to original order to identify quality issues that reached customers

### NCR Complete (Non-Conformance Report)
- **Purpose**: Documents quality failures and assigns accountability
- **Entry**: Marked "X" when NCR is issued to the inspector
- **Link**: Matched to Red Flag via Order Number

### Sewing Fail vs QC Fail
- **Sewing Fail**: Defect caught during sewing process (earlier detection)
- **QC Fail**: Defect made it through sewing, caught at final QC inspection
- **Important**: These track WHERE the fail was caught, not additional fails
- **KPI Value**: Ratio helps track effectiveness of sewing QC - higher Sewing Fail % = better upstream detection

### Repairs vs Scrap
- **Repairs**: Items with defects that were successfully fixed and passed QC
- **Scrap**: Items with defects that could not be salvaged (removed from final count)
- **Important**: Scrap = Total Fails. If something fails, it gets scrapped.

### Final Qty Calculation
```
Final Qty = Quantity - Scrap
```
Note: Repairs do NOT reduce Final Qty (repaired items pass and are counted)

---

## QC Inspectors

Current inspectors (as of JAN26):
- ABBY
- BRYCE
- CHRISTIAN
- DINA
- JACKIE
- JULIET
- PA/SEWING ASST.
- SHAUNDA
- SKYE

---

## Monthly KPIs

Metrics tracked on KPI sheets (by quarter):

| KPI | Description | Calculation |
|-----|-------------|-------------|
| Quality KPI - Pass Rate (Fails) | Overall pass rate | (Total Passed) / (Total Inspected) |
| Repair Rate (Fixes) | Rate of items needing repair | (Total Repairs) / (Total Inspected) |
| QC Fail Rate | Rate of fails caught at QC | (Total QC Fails) / (Total Scrap) |
| Sewn Resale Pass Rate | Pass rate for Bearse products | Bearse passed / Bearse inspected |
| Sewn Resale (Bearse) Repair Rate | Repair rate for Bearse | Bearse repairs / Bearse inspected |
| Resale (Non Sewn) Pass Rate | Pass rate for Resale items | Resale passed / Resale inspected |
| Total SS Products Inspected | Volume metric | Sum of SS Quantity |
| Total SS Fails | Fail count | Sum of SS Scrap (Fails = Scrap) |

---

---

## SKU Structure & Rollup Logic

### SKU Format
SKUs follow the pattern: `PARENT-COLOR` or `PARENT-COLOR-SIZE`

**Examples:**
- `AC-ESE-BK` → Parent: AC-ESE, Color: BK
- `PC-F20-BK-LG` → Parent: PC-F20, Color: BK, Size: LG

### Color Codes (Complete List - ONLY these, no others)
```
BK, CB, MC, MA, MB, MT, RG, WD, WG, TB, TD, TJ, RD, ML, NG, NP, RT
```
**Note:** CR is NOT a color code - it's a product line prefix (CR-AL, CR-FS, etc.)

### Size Codes
```
SM, MD, LG, XL, XXL, 05, 10, 15, 20, 25
```

### Parent SKU Rollup Rules

**Purpose:** Roll up color variants to analyze at the parent product level.

**Logic:**
1. Remove COLOR code only
2. Keep SIZE designation if present
3. Leave exceptions unchanged

**Examples:**
| Original SKU | Parent SKU | Rule Applied |
|--------------|------------|--------------|
| AC-ESE-BK | AC-ESE | Remove color (BK) |
| AC-ESE-CB | AC-ESE | Remove color (CB) |
| PC-F20-BK-LG | PC-F20-LG | Remove color (BK), keep size (LG) |
| PC-F20-MC-MD | PC-F20-MD | Remove color (MC), keep size (MD) |
| BU-LV120-CB-LG | BU-LV120-LG | Remove color (CB), keep size (LG) |
| PO-MS-TD | PO-MS | Remove color (TD) |
| AC-HK | AC-HK | No color code - unchanged |

### Exceptions (Do NOT Modify)
| SKU | Reason |
|-----|--------|
| PI-CB | CB is part of product name, not a color |
| MI-556-TR | TR is not a color code |
| MI-556-SN | SN is not a color code |
| Any SKU without color code | Already at parent level |

### Rollup Algorithm (Pseudocode)
```
# ONLY these color codes - no others unless explicitly added
colors = [BK, CB, MC, MA, MB, MT, RG, WD, WG, TB, TD, TJ, RD, ML, NG, NP, RT]
exceptions = [PI-CB, MI-556-TR, MI-556-SN]
# Note: CR is a product prefix, not a color code

function get_parent_sku(sku):
    if sku in exceptions:
        return sku

    parts = sku.split('-')
    result = []

    for part in parts:
        if part not in colors:
            result.append(part)

    return '-'.join(result)
```

---

## Analysis Views

### View 1: Parent SKU Rollup
- Aggregate metrics by parent SKU (color-agnostic)
- Identify problem products regardless of color variant
- Compare fail rates across product families

### View 2: By Inspector
- Track fails per inspector
- Monitor individual QC performance
- Identify training needs or patterns

---

## Common Analysis Queries

### By Stream
- Compare pass rates across SS, Bearse, Resale
- Identify which stream has highest fail rates

### By Inspector
- Inspector-level pass rates and fail counts
- Red Flag frequency by inspector (NCR tracking)

### By SKU
- Problem SKUs with high fail rates
- SKUs with recurring Red Flags

### By Time
- Month-over-month trend analysis
- Seasonal patterns in quality metrics

### Fail Origin Analysis
- Sewing Fail % vs QC Fail % for SS products
- Track improvement in upstream defect detection

---

## Notes for Analysis

1. **Row 0 is headers** - Skip when aggregating data
2. **Empty rows may exist** between data entries
3. **Three separate tables** per sheet - don't merge without adding Stream identifier
4. **Bearse/Resale have no Sewing Fail** - Column doesn't exist, not just empty
5. **Percentages may be formulas** - Reference calculated values, not raw
6. **Reference Lists sheet** - Used for dropdowns, ignore for analysis

---

# ONE Tracker Dashboard Web App

## Project Goal

Build a Streamlit web application that allows users to:
1. Upload the ONE Tracker Excel file
2. Select analysis options via checkboxes
3. View KPIs and insights based on their role
4. Identify problem areas and actionable items

---

## Tech Stack

| Component | Choice | Reason |
|-----------|--------|--------|
| Framework | **Streamlit** | Fast to build, Python-native, great for data apps, easy file upload |
| Data Processing | Pandas | Excel handling, aggregations, transformations |
| Visualization | Plotly / Streamlit native | Interactive charts, professional appearance |
| Hosting (optional) | Streamlit Community Cloud | Free, easy deployment |

### Local Development
```bash
pip install streamlit pandas plotly openpyxl
streamlit run app.py
```
No account required for local development.

---

## KPIs & Metrics

### Volume Metrics
| Metric | Calculation | Purpose |
|--------|-------------|---------|
| Total Products Inspected | Sum of Quantity | Overall throughput |
| Total Orders Processed | Count of unique Order Numbers | Workload indicator |
| Products per Inspector | Quantity / Inspector count | Workload distribution |
| Daily/Weekly Throughput | Quantity / Time period | Capacity planning |

### Quality Metrics
| Metric | Calculation | Purpose |
|--------|-------------|---------|
| Pass Rate | Final Qty / Quantity | Overall quality indicator |
| Fail Rate | Scrap / Quantity | Quality problem indicator (Fails = Scrap) |
| Repair Rate | Repairs / Quantity | Rework indicator |
| Scrap Rate | Scrap / Quantity | Waste/cost indicator (same as Fail Rate) |
| Sewing Detection Rate | Sewing Fail / Scrap | % of fails caught at sewing (early detection) |

### SKU Analysis
| Metric | Description |
|--------|-------------|
| Top 5 Parent SKUs by Fail Count | Highest volume of failures |
| Top 5 Parent SKUs by Fail % | Highest failure rate (with min volume threshold) |
| Top 5 Parent SKUs by Repair Count | Most rework required |
| Recurring Red Flag SKUs | Customer return patterns |
| Problem SKUs | High fail rate + high volume = priority |

### Inspector Performance
| Metric | Description |
|--------|-------------|
| Volume by Inspector | Products inspected per person |
| Pass Rate by Inspector | Quality consistency |
| Fails by Inspector | Error patterns |
| Red Flags/NCRs by Inspector | Customer-impacting issues |

### Trend Analysis
| Metric | Description |
|--------|-------------|
| Month-over-Month Pass Rate | Quality trend |
| Fail Rate Trend | Improving or declining? |
| Volume Trend | Capacity utilization |

---

## Role-Based Dashboard Views

### Production Manager (Primary View)
**Focus:** Overall production quality, output, and problem identification

**Key Metrics:**
- Total products inspected
- Overall pass/fail rate
- Scrap rate (cost impact)
- Top problem SKUs (fail count and fail %)
- Repair rate (rework overhead)
- Trend charts (quality over time)

**Insights:**
- SKUs needing immediate attention
- Quality trends (improving/declining)
- Capacity vs quality tradeoffs

### Operations Director
**Focus:** High-level KPIs, trends, business impact

**Key Metrics:**
- Executive summary cards (Pass Rate, Fail Rate, Volume)
- Cost of quality indicators (scrap, repairs)
- Customer impact (Red Flag count)
- Month-over-month trends
- Department comparison (if multiple streams)

**Insights:**
- Strategic quality issues
- Resource allocation needs
- Customer satisfaction indicators

### Sewing Manager
**Focus:** Upstream defect detection, sewing quality

**Key Metrics:**
- Sewing Fail rate
- Sewing Fail vs QC Fail ratio
- Top SKUs with sewing issues
- Sewing fail trends

**Insights:**
- Are defects being caught early?
- Which products have sewing issues?
- Training opportunities

### QC Manager
**Focus:** Inspector performance, inspection effectiveness

**Key Metrics:**
- Inspector-level pass rates
- Volume by inspector
- Red Flags/NCRs by inspector
- QC Fail patterns

**Insights:**
- Inspector performance comparison
- Training needs
- NCR accountability
- Workload balance

---

## App Structure

```
┌─────────────────────────────────────────────────────────────┐
│  ONE TRACKER DASHBOARD                                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  📁 UPLOAD SECTION                                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Drag & drop ONE Tracker Excel file here            │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  🎛️ FILTERS & OPTIONS                                       │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐    │
│  │ Role: [...v] │ │ Month: [..v] │ │ ☑ SS Stream Only │    │
│  └──────────────┘ └──────────────┘ └──────────────────┘    │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  📊 SUMMARY CARDS                                           │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐   │
│  │ Pass   │ │ Fail   │ │ Repair │ │ Scrap  │ │ Total  │   │
│  │ Rate   │ │ Rate   │ │ Rate   │ │ Rate   │ │ Insp.  │   │
│  │ 98.4%  │ │ 1.6%   │ │ 4.2%   │ │ 0.8%   │ │ 11,953 │   │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘   │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  📈 TREND CHART                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  [Pass Rate Over Time - Line Chart]                 │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  🔴 PROBLEM SKUs                     👤 INSPECTOR PERF     │
│  ┌─────────────────────────┐        ┌──────────────────┐   │
│  │ SKU      | Fail% | Vol  │        │ Name    | Pass%  │   │
│  │ PC-MTR   | 8.2%  | 450  │        │ ABBY    | 99.1%  │   │
│  │ BU-LV120 | 6.1%  | 320  │        │ BRYCE   | 98.7%  │   │
│  │ ...      | ...   | ...  │        │ ...     | ...    │   │
│  └─────────────────────────┘        └──────────────────┘   │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  💡 KEY INSIGHTS & ALERTS                                   │
│  • 3 SKUs have >5% fail rate - review manufacturing        │
│  • Red flags up 15% vs last month                          │
│  • Sewing catching 72% of defects (up from 68%)            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## File Structure (App)

```
ONE_Tracker/
├── .git/                         # Git repository
├── .gitignore                    # Excludes data files from repo
├── ONE_Tracker_Reference.md      # This documentation
├── ONE_Tracker_JAN26.xlsx        # Source data (local only, not in repo)
├── app.py                        # Main Streamlit application
├── requirements.txt              # Python dependencies
└── utils/
    ├── __init__.py               # Package init
    ├── data_loader.py            # Excel parsing, data cleaning
    ├── sku_utils.py              # Parent SKU rollup logic
    └── metrics.py                # KPI calculations
```

---

## Development Phases

### Phase 1: Core Functionality - COMPLETE
- [x] File upload and parsing
- [x] SS Stream data extraction
- [x] Basic metrics calculation
- [x] Summary cards display

### Phase 2: Production Manager View - COMPLETE
- [x] Pass/Fail rate metrics
- [x] Top problem SKUs table
- [x] Repair and scrap rates
- [x] Basic trend chart

### Phase 3: Additional Views - COMPLETE
- [x] Inspector performance table
- [x] Role-based view switching (4 roles)
- [x] Sewing vs QC fail analysis

### Phase 4: Insights & Polish - COMPLETE
- [x] Automated insights/alerts
- [x] Basic styling
- [x] Multi-month comparison (when multiple months selected)
- [ ] Export functionality (PDF/Excel) - Future

### Phase 5: Role-Based Enhancements (Feb 2026) - COMPLETE
- [x] On-time delivery metrics (Production Manager)
- [x] Recurring problem SKU detection - 6 month lookback (Sewing Manager)
- [x] Inspector SKU concentration alerts (QC Manager)
- [x] Month-over-month trend charts (Operations Director)
- [x] Month presets (Q1-Q4, YTD)
- [x] PA/SEWING ASST separated from comparisons
- [x] Former employee filtering
- [x] Repairs by Parent SKU (Sewing Manager)

---

## Dashboard Enhancement Requirements (Feb 2026 Session)

This section captures requirements gathered from stakeholder discussion for improving role-based dashboard views.

### Dashboard Focus

**SS Stream Only** - Dashboard focuses exclusively on in-house production (SS Stream). Bearse and Resale streams are not displayed.

---

### Performance Targets & Thresholds

| Metric | Target | Notes |
|--------|--------|-------|
| Fail Rate | ≤3% | Good month |
| Repair Rate | ≤3% | Good month |
| On-Time Delivery | ≥97% | Anything below is unacceptable |
| Min Units for Rate Tables | 10 | Prevent misleading rates from small samples |

**Color Coding:**
- Green = Pass / Good performance
- Red = Fail / Needs attention

---

### On-Time Delivery Metrics (NEW)

**Calculation:** Compare `Finished` date to `Due Date`
- Late = `Finished > Due Date` (no grace period)
- On-Time = `Finished <= Due Date`

**Metrics to Display:**
- On-Time Rate % = (On-Time Orders / Total Orders) × 100
- Total Late Orders (count)
- Total Days Late (sum of all late days)
- Average Days Late (Total Days Late / Late Orders)

**Purpose:** Production Manager uses this to challenge the team to improve each month.

---

### Multi-Month Analysis

**File Structure:** ONE Tracker contains multiple monthly sheets (JAN25, FEB25, ... JAN26, etc.)

**Recurring Problem SKU Detection:**
- Look back 6 months from the currently selected month
- Example: If viewing JAN26, analyze AUG25 through JAN26
- Use Parent SKU level (color has no bearing on construction)
- Flag SKUs that appear in top problem list for multiple months

---

### Inspector Analysis Rules

**PA/SEWING ASST:**
- Catch-all category for simpler packaging work (not full QC inspection)
- Consider excluding from inspector performance comparisons, or note they handle different work

**Former Employees:**
- Some inspector names may appear in historical data but not recent months
- These are former employees no longer with the company

**SKU Distribution Alert:**
- Flag if any inspector receives >50% of a specific Parent SKU
- Indicates uneven workload distribution
- Only meaningful with sufficient volume (suggest 20+ units of that Parent SKU)

---

### Role-Specific Requirements

#### Production Manager
**Usage Frequency:** Most frequent user (daily, weekly, or monthly)

**Key Responsibilities:**
- Works with Sewing Manager on getting reworks and fails under control
- Ranks SKUs that need to be addressed with more training, better instructions, or R&D design changes
- Monitors on-time delivery and challenges team to improve

**Key Metrics Needed:**
- On-time delivery rate and late order details
- Top problem SKUs (by fail count and fail rate)
- Fail rate, repair rate, scrap rate
- % of fails caught at sewing (inline detection)

---

#### Sewing Manager
**Focus:** Product-level issues, NOT inspector-level

**Key Responsibilities:**
- Identifies which products are causing the most issues in sewing
- Uses data to determine if products need: retraining, updated work instructions, or R&D design review

**Key Metrics Needed:**
- Recurring problem SKUs (appearing across multiple months)
- Top SKUs by sewing fail count
- Top SKUs by repair count (repairs = sewing rework = unplanned downtime)
- % caught at sewing vs % caught at QC

**Note:** Sewing Manager does NOT care which inspector found the fail, only which Parent SKU had the fail.

**Future Enhancement:** Cross-reference another document to match sewing machine operators with specific reworks/fails.

---

#### QC Manager
**Focus:** Inspector performance and inspection effectiveness

**Key Responsibilities:**
- Monitors how many fails are being found at QC (vs sewing)
- Tracks which inspectors are finding the most fails or reworks
- Uses discretion to interpret inspector data (knows staff tendencies)

**Key Metrics Needed:**
- Inspector comparison table (volume, fail rate, repair rate, NCRs, Red Flags)
- SKU distribution across inspectors (flag >50% concentration)
- NCRs and Red Flags by inspector
- % caught at sewing (goal: increase early detection)

**Comparison Fairness:** Compare inspectors within similar SKU mix. PA/SEWING ASST handles different (simpler) work.

---

#### Operations Director
**Focus:** 30,000 ft view - high-level metrics, minimal detail

**Key Responsibilities:**
- Strategic decisions on where to invest (training, tooling, process, R&D)
- Monitors customer risk (NCRs, Red Flags)

**Key Metrics Needed:**
- Overall pass rate, fail rate, repair rate
- Touch Rate (repairs + scrap) as COPQ proxy
- NCR and Red Flag counts
- Month-over-month trends for: NCRs, total fails, total reworks
- Top problem SKUs (still important at this level)
- On-time delivery summary

**Inspector Data:** Only show if there's a >50% SKU concentration issue. Otherwise, focus on SKU-level and overall metrics.

**Future Enhancement:** Cost of quality analysis using separate product cost data.

---

### Repairs Context

- **Who repairs:** Sewing team (not QC)
- **Impact:** Unplanned downtime, capacity drain
- **Effort:** Varies from quick fixes (seconds) to significant rework (minutes)
- **Priority:** Higher priority if order has a sales order reserved against it

---

### Red Flags & NCRs Context

- **Volume:** Rare, typically 2-10 per month
- **Relationship:** Red Flag always leads to NCR being issued
- **Purpose:** Escape signal (customer-impacting issue), not diagnostic
- **NCR:** Only an "X" marker with no root cause detail in this tracker

---

### Visual & UX Guidelines

**Charts:**
- Should be legible - avoid too many lines or data points too close together
- Consider weekly rollups if daily data is too noisy
- Line charts for trends, bar charts for comparisons

**Color Coding:**
- Green = Pass / Good / On target
- Red = Fail / Bad / Needs attention
- Yellow = Warning / Approaching threshold (optional)

**Data Tables:**
- Apply minimum volume thresholds to avoid misleading rates
- Sort by most relevant metric for each role

---

### Finalized Decisions

| Topic | Decision |
|-------|----------|
| **PA/SEWING ASST** | Exclude from inspector performance comparisons. Still display their volume to evaluate need for additional inspector. Also excluded from SKU concentration alerts. |
| **BRYCE (QC Manager)** | Excluded from SKU concentration alerts - intentionally focuses on BU items. |
| **Former employees** | Exclude from analysis if missing from most recent month. |
| **Blank Due Date** | Exclude order from on-time calculations, but display count of orders missing due dates as a data quality flag. |
| **Blank Finished date** | Will never happen - only completed orders are tracked. |
| **50% SKU concentration** | Parent SKU level. Only flag if Parent SKU has 10+ orders total. Excludes BRYCE and PA/SEWING ASST. |
| **Month selection** | Support BOTH single month AND multi-month selection. Add presets for Q1-Q4 for both 2025 and 2026, plus Year-to-Date (Jan-current, calendar year). |
| **Recurring problem SKU** | Parent SKU appearing in top 5 problem SKUs for 3+ of the last 6 months. |
| **Default month** | Most recent month in the uploaded file. |
| **Default role** | Production Manager. |
