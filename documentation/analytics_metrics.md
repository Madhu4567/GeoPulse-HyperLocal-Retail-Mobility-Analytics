# GeoPulse — Retail Analytics Metrics & Business Definitions

> **Document**: Analytics Metrics Dictionary  
> **Project**: GeoPulse — Hyper-Local Retail Mobility Analytics  
> **Phase**: Phase 3  
> **Last Updated**: 2026-11-25  

---

## 1. Core Retail Mobility Metrics

### 1.1 Total Footfall (Total Visits)
- **Technical Definition:** Count of distinct confirmed visit identifiers (`COUNT(DISTINCT visit_id)`).
- **Grain:** Visit event level.
- **Business Purpose:** Measures total store engagement traffic. A single customer visiting 3 times across a week contributes 3 to total footfall.
- **Analytical Rule:** Never use raw GPS pings (`COUNT(*)`) as footfall. One visit represents multiple continuous pings.

### 1.2 Unique Visitors (Patron Reach)
- **Technical Definition:** Count of distinct anonymized user identifiers (`COUNT(DISTINCT user_id)`).
- **Grain:** Customer level.
- **Business Purpose:** Measures net customer reach.
- **Relationship:** $\text{Unique Visitors} \le \text{Total Footfall}$.

### 1.3 Repeat Visitor Rate (%)
- **Technical Definition:**
  $$\text{Repeat Rate} = \frac{\text{Total Footfall} - \text{Unique Visitors}}{\text{Total Footfall}} \times 100\%$$
- **Business Purpose:** Quantifies customer retention and habitual visitation. High repeat rates indicate neighborhood loyalty or daily-necessity retail (cafes, convenience, groceries).

### 1.4 Average Dwell Time (Minutes)
- **Technical Definition:** Mean duration between visit arrival and departure timestamps:
  $$\text{Avg Dwell} = \frac{1}{N} \sum_{i=1}^{N} (T_{\text{departure}} - T_{\text{arrival}})$$
- **Business Purpose:** Distinguishes quick-stop convenience shopping ($5$–$15$ min) from experiential browsing or dining ($20$–$60$ min).

### 1.5 Peak Operational Hour
- **Technical Definition:** The hour of day ($0$–$23$) capturing the highest volume of visit arrivals for a given store:
  $$\text{Peak Hour} = \arg\max_{h} (\text{Hourly Visits}_h)$$
- **Business Purpose:** Guides store staffing, inventory restocking schedules, and flash promotions.

### 1.6 Weekend Lift Ratio
- **Technical Definition:** Ratio of normalized daily weekend traffic to normalized daily weekday traffic:
  $$\text{Weekend Lift} = \frac{\text{Weekend Visits} / 2}{\text{Weekday Visits} / 5}$$
- **Interpretation:**
  - $\text{Lift} > 1.0$: Weekend destination store (fashion, leisure, luxury).
  - $\text{Lift} < 1.0$: Commuter/weekday-driven store (office district coffee shops, quick-service lunch).

### 1.7 Commercial Zone Visit Density (Visits / $\text{km}^2$)
- **Technical Definition:** Total commercial zone footfall divided by true geodesic surface area:
  $$\text{Density} = \frac{\text{Total Zone Visits}}{\text{Zone Area } (\text{km}^2)}$$
- **Business Purpose:** Normalizes footfall across zones of unequal geographic size to identify retail hotspots.

---

## 2. Business Interpretation Guidelines & Caveats

1. **Synthetic Data Context:** All mobility signals and store coordinates in this prototype are synthetically generated for demonstration and architectural evaluation.
2. **Footfall $\neq$ Revenue:** High visitor traffic indicates customer footfall but does not account for shopping basket size, conversion rates, or average transaction value.
3. **Zoning $\neq$ Guaranteed Demand:** Commercial zoning reflects retail cluster density, not necessarily unmet consumer purchasing power.
