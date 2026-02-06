"""Export trained ML models for the FastAPI service."""

import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.tree import DecisionTreeClassifier


def load_data():
    """Load training data from local or remote source."""
    local_path = Path("Data Analysis/Datasets/dim_menu_items_cleaned.csv")
    
    if local_path.exists():
        print(f"Loading data from {local_path}")
        return pd.read_csv(local_path)
    
    print("Loading data from GitHub...")
    url = (
        "https://raw.githubusercontent.com/Radwa-Ayman239/"
        "MenueEngineering/refs/heads/main/"
        "Data%20Analysis%20/Datasets/dim_menu_items_cleaned.csv"
    )
    return pd.read_csv(url)


def prepare_data(df):
    """Clean data and engineer features."""
    required_cols = ["price", "purchases"]
    df = df.dropna(subset=required_cols)
    
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df["purchases"] = pd.to_numeric(df["purchases"], errors="coerce")
    df = df.dropna(subset=required_cols)
    
    # Feature engineering
    df["revenue"] = df["price"] * df["purchases"]
    df["estimated_cost"] = df["price"] * 0.40
    df["margin"] = df["price"] - df["estimated_cost"]
    
    return df


def create_labels(df):
    """Classify items using menu engineering matrix."""
    popularity_threshold = df["purchases"].median()
    profit_threshold = df["margin"].median()

def create_labels(df):
    """Classify items using menu engineering matrix."""
    popularity_threshold = df["purchases"].median()
    profit_threshold = df["margin"].median()
    
    def label(row):
        if row["purchases"] >= popularity_threshold and row["margin"] >= profit_threshold:
            return "Star"
        elif row["purchases"] >= popularity_threshold:
            return "Plowhorse"
        elif row["margin"] >= profit_threshold:
            return "Puzzle"
        return "Dog"
    
    df["menu_label"] = df.apply(label, axis=1)
    
    print("Category distribution:")
    for cat, count in df["menu_label"].value_counts().items():
        print(f"  {cat}: {count}")
    
    return df


def main():
    print("Menu Engineering Model Export\n")
    
    # Load and prepare data
    df = load_data()
    print(f"Loaded {len(df)} rows, columns: {df.columns.tolist()}\n")
    
    df = prepare_data(df)
    print(f"After cleaning: {len(df)} rows\n")
    
    df = create_labels(df)
    
    # Train model
    features = ["price", "purchases", "margin"]
    X = df[features].values
    y = df["menu_label"]
    
    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
    )
    
    print(f"Training samples: {len(X_train)}, Test samples: {len(X_test)}\n")
    
    model = DecisionTreeClassifier(max_depth=4, random_state=42)
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    print("Classification Report:")
    print(classification_report(y_test, y_pred, target_names=label_encoder.classes_))
    
    # Export models
    output_dir = Path("ml_service/models")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    classifier_path = output_dir / "menu_classifier.joblib"
    joblib.dump(model, classifier_path)
    print(f"Saved: {classifier_path}")
    
    encoder_path = output_dir / "label_encoder.joblib"
    joblib.dump(label_encoder, encoder_path)
    print(f"Saved: {encoder_path}")
    
    feature_info = {
        "features": features,
        "classes": label_encoder.classes_.tolist(),
        "model_type": "DecisionTreeClassifier",
        "max_depth": 4,
        "training_samples": len(X_train),
        "test_accuracy": float((y_pred == y_test).mean()),
    }
    
    info_path = output_dir / "model_info.json"
    with open(info_path, "w") as f:
        json.dump(feature_info, f, indent=2)
    print(f"Saved: {info_path}\n")
    
    # Verify
    loaded_model = joblib.load(classifier_path)
    loaded_encoder = joblib.load(encoder_path)
    
    test_item = [[129.0, 50, 77.4]]
    prediction = loaded_model.predict(test_item)[0]
    category = loaded_encoder.inverse_transform([prediction])[0]
    confidence = max(loaded_model.predict_proba(test_item)[0])
    
    print(f"Test prediction: {category} (confidence: {confidence:.2%})")
    print("Export complete!")


if __name__ == "__main__":
    main()
