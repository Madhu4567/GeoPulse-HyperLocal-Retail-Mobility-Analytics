from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data" / "processed"

geo = pd.read_csv(DATA_DIR / "store_overlap_analysis.csv")
mobility = pd.read_csv(DATA_DIR / "mobility_overlap_analysis.csv")

result = geo.merge(
    mobility,
    left_on=["store_id_1", "store_id_2"],
    right_on=["store1_id", "store2_id"],
    how="inner"
)

result["proximity_category"] = result["distance_km"].apply(
    lambda x: "High" if x <= 2 else "Medium" if x <= 3 else "Low"
)

result["potential_overlap"] = (
    (result["distance_km"] <= 3) &
    (result["jaccard_overlap_percentage"] >= 15)
)

output = DATA_DIR / "store_cannibalization_analysis.csv"
result.to_csv(output, index=False)

print("Cannibalization analysis completed!")
print("Total store pairs:", len(result))
print("Potential overlap pairs:", result["potential_overlap"].sum())
print("Output:", output)