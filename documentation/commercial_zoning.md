# GeoPulse — Commercial Zoning Methodology & Spatial Architecture

> **Document**: Commercial Zoning Specification  
> **Project**: GeoPulse — Hyper-Local Retail Mobility Analytics  
> **Phase**: Phase 3  
> **Last Updated**: 2026-11-25  

---

## 1. Study Area & Geographic Baseline

GeoPulse defines its primary study area within the **Manhattan Urban Core** in New York City:
- **Latitude Span:** $40.7000^\circ\text{N} \le \text{Lat} \le 40.8200^\circ\text{N}$
- **Longitude Span:** $-74.0200^\circ\text{W} \le \text{Lon} \le -73.9300^\circ\text{W}$
- **Coordinate Reference System:** WGS 84 (`EPSG:4326`)

To reflect real-world commercial concentration, retail stores and visitor mobility are clustered around six major commercial zoning sub-districts.

---

## 2. Commercial Zone Definitions

| Zone ID | Zone Name | Category / Type | Boundary Coordinates (WGS84 Lat, Lon) | Geodesic Area ($\text{km}^2$) |
|---|---|---|---|---|
| `ZN_001` | Midtown / Herald Square Retail Core | Shopping District | $[(40.7460, -73.9930) \to (40.7555, -73.9820)]$ | $0.98\text{ km}^2$ |
| `ZN_002` | SoHo Historic Commercial Corridor | Main Market | $[(40.7180, -74.0040) \to (40.7280, -73.9930)]$ | $1.03\text{ km}^2$ |
| `ZN_003` | Union Square / Flatiron Hub | Mixed Commercial-Residential | $[(40.7330, -73.9950) \to (40.7430, -73.9840)]$ | $1.03\text{ km}^2$ |
| `ZN_004` | Financial District Commerce Center | Business District | $[(40.7040, -74.0150) \to (40.7130, -74.0030)]$ | $1.01\text{ km}^2$ |
| `ZN_005` | Upper East Side Luxury Corridor | Retail Complex | $[(40.7680, -73.9630) \to (40.7790, -73.9500)]$ | $1.34\text{ km}^2$ |
| `ZN_006` | Chelsea / Meatpacking Highline District | Local Market | $[(40.7370, -74.0110) \to (40.7470, -73.9990)]$ | $1.12\text{ km}^2$ |

---

## 3. Geodesic Surface Area Calculation

To strictly adhere to geospatial accuracy standards, polygon areas are **never computed by multiplying degrees squared**:
$$\text{Area} = R^2 \times \frac{1}{2} \left| \sum_{i=1}^{n} (\lambda_{i+1} - \lambda_{i-1}) \sin(\phi_i) \right|$$
where $R = 6371.0088\text{ km}$ (IUGG mean spherical Earth radius), $\phi$ is latitude in radians, and $\lambda$ is longitude in radians. This guarantees metric surface accuracy on the spherical reference globe.

---

## 4. Spatial Point-in-Polygon Engine

Store assignment utilizes a high-precision ray-casting algorithm implemented in `analytics/commercial_zoning/zone_validator.py`.
- For each store coordinate $(Lat_s, Lon_s)$, a horizontal ray is cast eastward.
- Crossings with polygon segments are evaluated with edge-case handling for vertices.
- **Unmatched Store Rule:** Stores located in peripheral or transitional corridors outside defined zone polygons are tagged as `UNZONED` (`zone_name = 'Outside Commercial Zones'`). They are strictly preserved to maintain 100% store catalog completeness.

---

## 5. Store-to-Zone Spatial Mapping Results

From the 30 active stores evaluated:
- **Stores Inside Commercial Zones:** 20 stores ($66.7\%$)
- **Stores Outside Commercial Zones (Peripheral):** 10 stores ($33.3\%$)
- **Distribution across Zones:**
  - `ZN_003` (Union Square / Flatiron Hub): 6 stores
  - `ZN_001` (Midtown / Herald Square Retail Core): 5 stores
  - `ZN_005` (Upper East Side Luxury Corridor): 5 stores
  - `ZN_002` (SoHo Historic Commercial Corridor): 3 stores
  - `ZN_004` (Financial District Commerce Center): 1 store
  - `ZN_006` (Chelsea / Meatpacking Highline District): 0 stores (residential buffer)

---

## 6. Visit-to-Zone Spatial Mapping & Footfall Conservation

Detected visits ($3,487$ confirmed visits) are mapped to commercial zones through their confirmed store assignment:
- **Total Input Visits:** $3,487$
- **Total Output Mapped Visits:** $3,487$ (100% conservation)
- **Visits inside Commercial Zones:** $2,321$ ($66.56\%$)
- **Visits in Unzoned / Peripheral Stores:** $1,166$ ($33.44\%$)
- **Cardinality:** Exactly 1-to-1. No visit is duplicated or dropped.

---

## 7. Commercial Zone Footfall Performance Summary

| Zone ID | Zone Name | Zone Type | Area ($\text{km}^2$) | Stores | Total Visits | Unique Patrons | Avg Dwell (min) | Top Category | Daily Footfall | Density (Visits/$\text{km}^2$) |
|---|---|---|---|---|---|---|---|---|---|---|
| `ZN_001` | Midtown / Herald Square | Shopping District | 0.98 | 5 | 684 | 366 | 23.02 | Cafe & Bakery | 85.50 | 698.81 |
| `ZN_003` | Union Sq / Flatiron | Mixed Commercial | 1.03 | 6 | 674 | 379 | 23.12 | Convenience | 84.25 | 654.05 |
| `ZN_005` | Upper East Side | Retail Complex | 1.34 | 5 | 544 | 332 | 22.43 | Dept Store | 68.00 | 406.27 |
| `ZN_002` | SoHo Historic Corridor | Main Market | 1.03 | 3 | 285 | 219 | 22.58 | Pharmacy | 35.62 | 276.48 |
| `ZN_004` | Financial District | Business District | 1.01 | 1 | 134 | 117 | 22.81 | Cafe & Bakery | 16.75 | 132.38 |
| `ZN_006` | Chelsea / Meatpacking | Local Market | 1.12 | 0 | 0 | 0 | 0.00 | N/A | 0.00 | 0.00 |
