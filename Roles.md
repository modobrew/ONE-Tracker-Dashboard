# ONE Tracker Dashboard — Role-Based Output Spec (for Claude Code)

## Goal

You already have a working dashboard. This spec tells Claude Code **what each role-specific dashboard view should output** (KPIs, tables, charts, and the auto-generated “Key Insights” bullets).

This is **output-only**: assume the existing data pipeline + filters remain in place.

---

## 1) Global Controls (apply to all roles)

### Required Filters

* **Date range** (default: current month) using `Finished` date
* **Month selector** (shortcut)
* **SKU / Parent SKU** (multi-select)
* **Inspector** (multi-select)
* **Order Number / Lot Number** (search)
* Toggles:

  * **Red Flag only**
  * **NCR only**

**Note:** Dashboard focuses on SS Stream only (in-house production).

### Standard Threshold Settings (editable in UI)

* `min_units_for_rate_tables` (default **10**) — used to prevent tiny denominators
* `attention_fail_rate` (default **5%**) — flag SKUs/inspectors above this
* `attention_repair_rate` (default **5%**)
* `attention_scrap_rate` (default **2%**)

---

## 2) Common Metric Definitions (use everywhere)

All rates must be **weighted by units** (totals-based), not averages of row-level percentages.

Let:

* `Inspected = sum(Quantity)`
* `Repairs = sum(Repairs)`
* `Scrap = sum(Scrap)` if present else `sum(max(Quantity - Final Qty, 0))`
* `FinalQty = sum(Final Qty)`
* `QCFail = sum(QC Fail)`
* `SewFail = sum(Sewing Fail)`
* `Orders = count(distinct Order Number)`
* `RedFlags = count(rows where Red Flag not blank)`
* `NCRs = count(rows where NCR Complete not blank (e.g., "X"))`

### Core rates

* **Pass Rate %** = `(FinalQty / Inspected) * 100`
* **Repair Rate %** = `(Repairs / Inspected) * 100`
* **Scrap Rate %** = `(Scrap / Inspected) * 100`

### Fail Rate

* **Fail Rate %** = `(Scrap / Inspected) * 100`

**Important:** Scrap = Total Fails. If something fails, it gets scrapped.

### Defect detection location (WHERE fails were caught)

Sewing Fail and QC Fail track **where** the defect was detected, not separate fail counts. Their sum should approximately equal Scrap.

* **% Caught at Sewing** = if Scrap > 0: `(SewFail / Scrap) * 100` else: `N/A`
* **% Caught at QC** = if Scrap > 0: `(QCFail / Scrap) * 100` else: `N/A`

Higher "% Caught at Sewing" = better upstream detection (catching defects earlier is good).

---

## 3) Shared Section: Top-of-Page "Context Line"

Each role view should show a small context line like:

* `Analyzing: {MonthRange} | SS Stream | {Optional SKU/Inspector Filters}`

---

# 4) Role Views

## A) Production Manager View

**Purpose:** Keep output high without quietly generating rework/scrap chaos. Prioritize **where to focus today/this week**.

### A1) Summary Metric Cards (must display)

* **Pass Rate %**
* **Fail Rate %**
* **Repair Rate %**
* **Scrap Rate %**
* **Total Inspected**
* **Total Orders**
* **Total Fails** (= Scrap)
* **Total Repairs**
* **Total Scrap**
* **Red Flags**

### A2) Key Insights (auto-generated bullets)

Generate 3–6 bullets using these rules (show only bullets that trigger):

* ✅ If Pass Rate ≥ 98%: “Strong pass rate of {PassRate}%.”
* ⚠️ If Repair Rate ≥ attention_repair_rate: “Repair rate is elevated at {RepairRate}% — rework load is consuming capacity.”
* 🔥 If Scrap Rate ≥ attention_scrap_rate: “Scrap rate is elevated at {ScrapRate}% — investigate containment on highest-fail SKUs.”
* 🧭 If Scrap > 0: "{SewCatch}% of fails were caught at sewing (inline detection)."
* 🚩 If NCRs > 0 or RedFlags > 0: “{NCRs} customer returns (NCR) and {RedFlags} red flags in this period.”
* 🧨 If count(SKUs with Fail Rate ≥ attention_fail_rate and units ≥ min_units_for_rate_tables) > 0: “{n} SKUs exceed {attention_fail_rate}% fail rate — review manufacturing stability.”

### A3) Visuals (recommended)

* Line: **Daily Pass Rate %**
* Line: **Daily Repair Rate %**
* Line: **Daily Scrap Rate %**

### A4) Tables (must display)

1. **Top Problem SKUs (by Fail Count)**

   * Columns: Parent SKU, Qty Inspected, Fail Units, Fail Rate %
2. **Top Problem SKUs (by Fail Rate)**

   * Apply filter: Qty Inspected ≥ `min_units_for_rate_tables`
   * Columns: Parent SKU, Qty Inspected, Fail Units, Fail Rate %
3. **Red Flag / NCR Orders** (only when toggles active or count > 0)

   * Columns: Order Number, Lot Number, Finished, SKU, Qty, Repairs, QC Fail, Sewing Fail, Inspector, Red Flag, NCR Complete

---

## B) QC Manager View

**Purpose:** Quality system health. Focus on **escape risk (NCR), inspector calibration, and inspection effectiveness**.

### B1) Summary Metric Cards (must display)

* **Pass Rate %**
* **% Caught at QC** (QCFail share of Scrap — lower is better, means more caught at sewing)
* **Repair Rate %**
* **Scrap Rate %**
* **NCRs**
* **Red Flags**
* **Total Inspected**
* **Total Fails** (= Scrap)

### B2) Key Insights (auto-generated bullets)

* 🚨 If NCRs > 0: "{NCRs} NCRs flagged — review SKUs + inspectors with highest concentration."
* ⚖️ If inspector variance is high: "Inspector outcomes vary significantly — verify calibration and SKU mix."

  * Variance trigger suggestion: stdev of inspector fail rate > threshold OR top vs bottom differs by > 2x (only compare inspectors with ≥ min_units_for_rate_tables units)
* 🧭 If Scrap > 0: "{SewCatch}% of fails caught at sewing (goal: increase early detection)."

### B3) Visuals (recommended)

* Line: **Daily NCR count** (even if sparse)
* Line: **Daily Final QC Fail Rate**
* Bar: **NCRs by SKU**
* Bar: **NCRs by Inspector**

### B4) Tables (must display)

1. **Inspector Summary (Fair Comparison)**

   * Filter inspectors with Qty Inspected ≥ `min_units_for_rate_tables`
   * Columns: Inspector, Qty Inspected, Fail Rate %, Repair Rate %, Scrap Rate %, NCRs, Red Flags
   * UI warning note: "Compare within similar SKU mix for fairness."
2. **SKU Quality Summary**

   * Columns: SKU, Qty Inspected, Fail Units, Repairs, Fail Rate %, Repair Rate %, Scrap Rate %, NCRs
3. **NCR List** (filtered)

   * Columns: Order, Lot, Finished, SKU, Inspector, Qty, Fail/Repair counts, Red Flag

---

## C) Sewing Manager View

**Purpose:** Reduce defects at the source and improve **inline detection** so final QC isn’t the first real inspection.

### C1) Summary Metric Cards (must display)

* **% Caught at Sewing** (higher is better — early detection)
* **Sewing Fail Count** (SewFail)
* **QC Fail Count** (QCFail)
* **Fail Rate %** (Scrap / Inspected)
* **Repair Rate %** (because repairs are sewing touch labor)
* **Total Inspected**
* **Total Fails** (= Scrap)

### C2) Key Insights (auto-generated bullets)

* 🧭 If Scrap > 0: "Inline caught {SewCatch}% of fails — raise this by tightening in-line checks."
* ⚠️ If QCFail > SewFail: "More fails are being caught at final QC than in-line — add/adjust in-line checkpoints."
* 🧨 If any SKU has high leakage: "{n} SKUs show high final-QC leakage (QCFail share > 50%)."
* 🔧 If Repair Rate ≥ attention_repair_rate: "Repair rate {RepairRate}% is high — review top SKUs driving repairs."

### C3) Visuals (recommended)

* Stacked bar (by day or week): **SewFail vs QCFail** (defects caught inline vs final)
* Line: **% Caught at Sewing** trend

### C4) Tables (must display)

1. **Top SKUs by Sewing Fail Count**

   * Columns: SKU, Qty Inspected, Sewing Fail, Sewing Fail Rate %
2. **Top SKUs by QC Fail Count** (fails caught late)

   * Filter: Qty Inspected ≥ `min_units_for_rate_tables`
   * Columns: SKU, Qty Inspected, QC Fail, Sewing Fail, % Caught at Sewing
3. **Top Repair Drivers**

   * Columns: SKU, Qty Inspected, Repairs, Repair Rate %

---

## D) Operations Director View

**Purpose:** System-wide decisions: where to invest (training/tooling/process/NPD), and where customer risk is rising.

### D1) Summary Metric Cards (must display)

* **Total Inspected**
* **Pass Rate %**
* **Touch Rate %** = `((Repairs + Scrap) / Inspected) * 100`
* **Scrap Rate %**
* **NCRs**
* **Red Flags**
* **Top 1–3 SKUs by Touch Units** (display as small callouts)

### D2) Key Insights (auto-generated bullets)

* 📈 "Touch rate is {TouchRate}% (repairs + scrap) — proxy for COPQ labor drag."
* 🚨 If NCRs rising vs prior month: "NCRs increased vs last month — review containment and systemic root causes."
* 🧭 If Scrap > 0: "Inline capture is {SewCatch}% — earlier detection reduces COPQ and customer escape risk."

### D3) Visuals (recommended)

* Line: **Monthly Pass Rate %** (12-month view if available)
* Line: **Monthly Touch Rate %**
* Bar: **NCRs by SKU**
* Bar: **Top SKUs by Touch Units**

### D4) Tables (must display)

1. **SKU Investment List** (ranked)

   * Sort by Touch Units (Repairs + Scrap)
   * Columns: SKU, Qty Inspected, Repairs, Scrap, Touch Units, Touch Rate %, NCRs
2. **Inspector Summary (Contextual)**

   * Same as QC Manager view but default filter is "all inspectors" and show a caution note

---

## 5) Role Selector Behavior

* Dashboard must allow selecting a **Role View** from: Production Manager, QC Manager, Sewing Manager, Operations Director.
* Changing role view:

  * swaps which sections are visible
  * preserves global filters
  * sets role-appropriate default sorting (e.g., Production: top fails; Sewing: % caught at sewing; QC: NCR; OD: touch units)

---

## 6) Notes / Guardrails

* NCR is only an "X" with no root cause. Treat it as an **escape signal**, not a diagnostic.
* Inspector comparisons must be **normalized** (min units threshold + optional SKU stratification).
* Prefer computed metrics over stored `Pass %` / `Repair %` columns.
* Dashboard focuses on SS Stream only (in-house production).
