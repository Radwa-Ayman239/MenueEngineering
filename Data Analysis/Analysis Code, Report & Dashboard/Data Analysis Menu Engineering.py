# %%
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
from datetime import datetime

# Configure settings
warnings.filterwarnings('ignore')
sns.set_style('whitegrid')
plt.rcParams['figure.figsize'] = (12, 6)
# %matplotlib inline

print("Libraries imported successfully!")
# %%

# %%
import pandas as pd

# === 1) Load dataset from GitHub ===
url = "https://raw.githubusercontent.com/Radwa-Ayman239/MenueEngineering/refs/heads/main/Data%20Analysis/Datasets/dim_items_cleaned.csv"
items_df = pd.read_csv(url)

# === 2) Inspect columns (optional) ===
print("Columns in dataset:", items_df.columns.tolist())

# === 3) We assume these core columns exist ===
# If names differ, adjust accordingly.
# Typical columns needed:
# - item_id / id
# - item_name (or name/title)
# - price
# - cost (if exists; if not, approximate or drop margin calc)
# - quantity_sold (purchases)

# Rename columns for consistency (adjust if different names in your file)
items_df = items_df.rename(columns={
    "id": "item_id",
    "title": "item_name",
    "price": "price",
    "cost": "cost",
    "quantity_sold": "purchases"
})

# === 4) Compute core metrics ===

# If cost column is missing, you can fill with zero or a default cost
if "cost" not in items_df.columns:
    items_df["cost"] = 0

items_df["revenue"] = items_df["price"] * items_df["purchases"]
items_df["profit"] = (items_df["price"] - items_df["cost"]) * items_df["purchases"]

# Optional: text / description lengths (useful for descriptive insights)
if "description" in items_df.columns:
    items_df["desc_length"] = items_df["description"].astype(str).str.len()
else:
    items_df["desc_length"] = 0

# === 5) Categorize using Menu Engineering thresholds ===
# Popularity threshold = median purchases
pop_median = items_df["purchases"].median()

# Profit threshold = median profit
profit_median = items_df["profit"].median()

def categorize(row):
    if row["purchases"] >= pop_median and row["profit"] >= profit_median:
        return "Star"
    elif row["purchases"] >= pop_median and row["profit"] < profit_median:
        return "Plowhorse"
    elif row["purchases"] < pop_median and row["profit"] >= profit_median:
        return "Puzzle"
    else:
        return "Dog"

items_df["category"] = items_df.apply(categorize, axis=1)

# === 6) Select only necessary columns for the model ===
items_df_cleaned = items_df[[
    "item_id",
    "item_name",
    "price",
    "purchases",
    "revenue",
    "profit",
    "category"
]]

# Optional: if description exists and you want to keep it:
if "description" in items_df.columns:
    items_df_cleaned["description"] = items_df["description"]

# Save to a new CSV that you can feed into your model
items_df_cleaned.to_csv("menu_engineering_input_items.csv", index=False)

print("Processed dataset ready — saved as menu_engineering_input.csv")
print(items_df_cleaned.head())

# %%

# %%

# %%
import pandas as pd

# === 1) Load dataset with better error handling ===
url = "https://raw.githubusercontent.com/Radwa-Ayman239/MenueEngineering/refs/heads/main/Data%20Analysis/Datasets/dim_items_cleaned.csv"

df = pd.read_csv(url, quotechar='"', skipinitialspace=True, on_bad_lines='warn')

# === 2) DIAGNOSTIC: Check for actual missing values ===
print("=== DIAGNOSTIC INFO ===")
print(f"Total rows: {len(df)}")
print(f"\nMissing descriptions (NaN): {df['description'].isna().sum()}")
print(f"Empty string descriptions: {(df['description'] == '').sum()}")

# === 3) Select columns ===
df = df[[
    "id",
    "title",
    "description",
    "price",
    "purchases"
]]

# === 4) Compute description length and clean ===
df["description_clean"] = df["description"].fillna("").str.strip()
df["desc_length"] = df["description_clean"].str.len()

# Show items with zero-length descriptions BEFORE filtering
zero_length = df[df["desc_length"] == 0]
print(f"\n=== Items with zero-length descriptions: {len(zero_length)} ===")
if len(zero_length) > 0:
    print(zero_length[["id", "title", "description"]].head(10))

# === 5) FILTER OUT items with missing/empty descriptions ===
df = df[df["desc_length"] > 0].copy()
print(f"\n=== After filtering: {len(df)} items remaining ===")

# === 6) Analyze Description Paradox ===
median_purchases = df["purchases"].median()
df["sales_group"] = df["purchases"].apply(
    lambda x: "Top Seller" if x >= median_purchases else "Low Seller"
)

# Compare average description length
desc_analysis = (
    df.groupby("sales_group")["desc_length"]
      .mean()
      .reset_index()
)
print("\nAverage Description Length by Sales Group:")
print(desc_analysis)

print("\nDescription Length Statistics by Sales Group:")
print(df.groupby("sales_group")["desc_length"].describe())

# === 7) Prepare dataset for Menu Engineering Model ===
df_model = df.drop(columns=["description_clean", "sales_group"])

# === 8) Save cleaned dataset ===
df_model.to_csv("menu_engineering_desc_cleaned.csv", index=False)
print("\n=== Model-ready dataset saved! ===")
print(df_model.head())
print(f"\nTotal items in final dataset: {len(df_model)}")
print(f"\nDescription length distribution:")
print(df_model["desc_length"].describe())
# %%
new_items_url = "https://raw.githubusercontent.com/Radwa-Ayman239/MenueEngineering/refs/heads/main/Data%20Analysis/Datasets/menu_engineering_input_items.csv"
new_items_df = pd.read_csv(new_items_url)
# === Filter Plowhorses ===
plowhorses_df = new_items_df[new_items_df["category"] == "Plowhorse"].copy()

if (plowhorses_df["purchases"] != 0).any():

    plowhorses_df["cost"] = plowhorses_df["price"] - plowhorses_df["revenue"] /plowhorses_df["purchases"]
else:
    plowhorses_df["cost"] = plowhorses_df["price"]
# === Scenario 1: Increase price by 5% ===
plowhorses_df["price_up_5"] = plowhorses_df["price"] * 1.05
plowhorses_df["profit_price_up"] = (
    plowhorses_df["price_up_5"] - plowhorses_df["cost"]
) * plowhorses_df["purchases"]

# === Scenario 2: Reduce cost by 5% ===
plowhorses_df["cost_down_5"] = plowhorses_df["cost"] * 0.95
plowhorses_df["profit_cost_down"] = (
    plowhorses_df["price"] - plowhorses_df["cost_down_5"]
) * plowhorses_df["purchases"]

# === Keep only useful columns ===
whatif_df = plowhorses_df[[
    "item_id",
    "item_name",
    "profit",
    "profit_price_up",
    "profit_cost_down"
]]

whatif_df.to_csv("menu_engineering_plowhorse_whatif.csv", index=False)

print("Saved as menu_engineering_plowhorse_whatif.csv")


# %%

new_items_url = "https://raw.githubusercontent.com/Radwa-Ayman239/MenueEngineering/refs/heads/main/Data%20Analysis/Datasets/menu_engineering_input_items.csv"
new_items_df = pd.read_csv(new_items_url)
# === Filter Plowhorses ===
dogs_df = new_items_df[new_items_df["category"] == "Dog"].copy()# === Filter Dogs ===


# === Profit contribution ===
total_profit = new_items_df["profit"].sum()
dogs_df["profit_share"] = dogs_df["profit"] / total_profit

# === Model-ready dataset ===
dogs_model_df = dogs_df[[
    "item_id",
    "item_name",
    "profit",
    "profit_share"
]]

dogs_model_df.to_csv("menu_engineering_dogs.csv", index=False)

print("Saved as menu_engineering_dogs.csv")
