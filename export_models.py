"""
Export trained ML models for the FastAPI service.

This script trains the Decision Tree model using the same logic as the notebook
and exports it to the ml_service/models directory.

Usage:
    python export_models.py

Or add the export code at the end of your Jupyter notebook.
"""

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report
import joblib
from pathlib import Path


def main():
    print("=" * 50)
    print("Menu Engineering Model Export")
    print("=" * 50)

    # --------------------------------------------------
    # 1. LOAD DATA
    # --------------------------------------------------
    print("\n📥 Loading data...")

    # Try local file first, then GitHub
    local_path = Path("Data Analysis/Datasets/dim_menu_items_cleaned.csv")

    if local_path.exists():
        print(f"   Using local file: {local_path}")
        df = pd.read_csv(local_path)
    else:
        print("   Fetching from GitHub...")
        url = (
            "https://raw.githubusercontent.com/Radwa-Ayman239/"
            "MenueEngineering/refs/heads/main/"
            "Data%20Analysis%20/Datasets/dim_menu_items_cleaned.csv"
        )
        df = pd.read_csv(url)

    print(f"   Loaded {len(df)} rows")
    print(f"   Columns: {df.columns.tolist()}")

    # --------------------------------------------------
    # 2. BASIC CLEANING
    # --------------------------------------------------
    print("\n🧹 Cleaning data...")

    required_cols = ["price", "purchases"]
    df = df.dropna(subset=required_cols)

    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df["purchases"] = pd.to_numeric(df["purchases"], errors="coerce")
    df = df.dropna(subset=required_cols)

    print(f"   After cleaning: {len(df)} rows")

    # --------------------------------------------------
    # 3. FEATURE ENGINEERING
    # --------------------------------------------------
    print("\n⚙️ Engineering features...")

    # Revenue
    df["revenue"] = df["price"] * df["purchases"]

    # Estimated cost (40% food cost assumption)
    df["estimated_cost"] = df["price"] * 0.40

    # Contribution margin
    df["margin"] = df["price"] - df["estimated_cost"]

    # --------------------------------------------------
    # 4. CREATE MENU ENGINEERING LABELS
    # --------------------------------------------------
    print("\n🏷️ Creating menu engineering labels...")

    popularity_threshold = df["purchases"].median()
    profit_threshold = df["margin"].median()

    print(f"   Popularity threshold (median purchases): {popularity_threshold}")
    print(f"   Profit threshold (median margin): {profit_threshold:.2f}")

    def menu_engineering_label(row):
        if (
            row["purchases"] >= popularity_threshold
            and row["margin"] >= profit_threshold
        ):
            return "Star"
        elif (
            row["purchases"] >= popularity_threshold
            and row["margin"] < profit_threshold
        ):
            return "Plowhorse"
        elif (
            row["purchases"] < popularity_threshold
            and row["margin"] >= profit_threshold
        ):
            return "Puzzle"
        else:
            return "Dog"

    df["menu_label"] = df.apply(menu_engineering_label, axis=1)

    print("\n   Category distribution:")
    for cat, count in df["menu_label"].value_counts().items():
        print(f"      {cat}: {count}")

    # --------------------------------------------------
    # 5. PREPARE DATA FOR MODEL
    # --------------------------------------------------
    print("\n📊 Preparing training data...")

    features = ["price", "purchases", "margin"]
    X = df[features]
    y = df["menu_label"]

    # Encode labels
    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)

    print(f"   Features: {features}")
    print(f"   Label classes: {label_encoder.classes_.tolist()}")

    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
    )

    print(f"   Training samples: {len(X_train)}")
    print(f"   Test samples: {len(X_test)}")

    # --------------------------------------------------
    # 6. TRAIN MODEL
    # --------------------------------------------------
    print("\n🤖 Training Decision Tree model...")

    model = DecisionTreeClassifier(max_depth=4, random_state=42)
    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)

    print("\n📈 Classification Report:")
    print(classification_report(y_test, y_pred, target_names=label_encoder.classes_))

    # --------------------------------------------------
    # 7. EXPORT MODELS
    # --------------------------------------------------
    print("\n💾 Exporting models...")

    # Create output directory
    output_dir = Path("ml_service/models")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save classifier
    classifier_path = output_dir / "menu_classifier.joblib"
    joblib.dump(model, classifier_path)
    print(f"   ✅ Saved: {classifier_path}")

    # Save label encoder
    encoder_path = output_dir / "label_encoder.joblib"
    joblib.dump(label_encoder, encoder_path)
    print(f"   ✅ Saved: {encoder_path}")

    # Save feature names for reference
    feature_info = {
        "features": features,
        "classes": label_encoder.classes_.tolist(),
        "model_type": "DecisionTreeClassifier",
        "max_depth": 4,
        "training_samples": len(X_train),
        "test_accuracy": (y_pred == y_test).mean(),
    }

    import json

    info_path = output_dir / "model_info.json"
    with open(info_path, "w") as f:
        json.dump(feature_info, f, indent=2)
    print(f"   ✅ Saved: {info_path}")

    # --------------------------------------------------
    # 8. VERIFY EXPORT
    # --------------------------------------------------
    print("\n🔍 Verifying export...")

    loaded_model = joblib.load(classifier_path)
    loaded_encoder = joblib.load(encoder_path)

    # Test prediction
    test_item = [[129.0, 50, 77.4]]  # price, purchases, margin
    prediction = loaded_model.predict(test_item)[0]
    category = loaded_encoder.inverse_transform([prediction])[0]
    confidence = max(loaded_model.predict_proba(test_item)[0])

    print(f"   Test prediction: {category} (confidence: {confidence:.2%})")

    print("\n" + "=" * 50)
    print("✅ Export complete! Models saved to ml_service/models/")
    print("=" * 50)
    print("\nYou can now start the ML service:")
    print("   docker-compose up ml_service")


if __name__ == "__main__":
    main()
