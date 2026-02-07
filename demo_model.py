"""
Interactive demo to test the Menu Engineering ML model.

Usage:
    python demo_model.py              # Interactive mode
    python demo_model.py --file data.csv  # Batch mode with CSV
"""

import argparse
import requests
import pandas as pd
from pathlib import Path

ML_SERVICE_URL = "http://localhost:8001"


def predict_single(price: float, purchases: int, margin: float = None):
    """Predict category for a single item."""
    if margin is None:
        margin = price * 0.6  # Default 40% food cost

    item = {
        "price": price,
        "purchases": purchases,
        "margin": margin,
        "description_length": 30,
    }

    try:
        response = requests.post(f"{ML_SERVICE_URL}/predict", json=item, timeout=10)
        if response.status_code == 200:
            return response.json()
        return {"error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}


def predict_batch(items: list[dict]):
    """Predict categories for multiple items."""
    batch = {"items": items}

    try:
        response = requests.post(
            f"{ML_SERVICE_URL}/batch-predict", json=batch, timeout=30
        )
        if response.status_code == 200:
            return response.json()["predictions"]
        return {"error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}


def process_csv(file_path: str):
    """Process a CSV file and add predictions."""
    df = pd.read_csv(file_path)

    # Check for required columns
    required = ["price", "purchases"]
    missing = [col for col in required if col not in df.columns]
    if missing:
        print(f"Error: Missing columns: {missing}")
        print(f"Available columns: {df.columns.tolist()}")
        return

    print(f"Loaded {len(df)} items from {file_path}")

    # Calculate margin if not present
    if "margin" not in df.columns:
        df["margin"] = df["price"] * 0.6
        print("Calculated margin using 40% food cost assumption")

    # Prepare items for batch prediction
    items = []
    for _, row in df.iterrows():
        items.append(
            {
                "price": float(row["price"]),
                "purchases": int(row["purchases"]),
                "margin": float(row["margin"]),
                "description_length": 30,
            }
        )

    print(f"Sending {len(items)} items to ML service...")
    predictions = predict_batch(items)

    if isinstance(predictions, dict) and "error" in predictions:
        print(f"Error: {predictions['error']}")
        return

    # Add predictions to dataframe
    df["predicted_category"] = [p["category"] for p in predictions]
    df["confidence"] = [p["confidence"] for p in predictions]

    # Summary
    print("\n" + "=" * 50)
    print("PREDICTION SUMMARY")
    print("=" * 50)

    for cat in ["Star", "Plowhorse", "Puzzle", "Dog"]:
        count = (df["predicted_category"] == cat).sum()
        pct = count / len(df) * 100
        print(f"  {cat:12} {count:5} items ({pct:.1f}%)")

    # Save output
    output_path = Path(file_path).stem + "_predictions.csv"
    df.to_csv(output_path, index=False)
    print(f"\nResults saved to: {output_path}")

    # Show sample
    print("\nSample predictions:")
    sample_cols = (
        ["title", "price", "purchases", "predicted_category", "confidence"]
        if "title" in df.columns
        else ["price", "purchases", "predicted_category", "confidence"]
    )
    print(df[sample_cols].head(10).to_string(index=False))


def interactive_mode():
    """Interactive mode for testing predictions."""
    print("=" * 50)
    print("Menu Engineering ML Model - Interactive Demo")
    print("=" * 50)
    print("\nEnter item details to get predictions.")
    print("Type 'quit' to exit.\n")

    while True:
        try:
            # Get input
            price_input = input("Price: ").strip()
            if price_input.lower() == "quit":
                break
            price = float(price_input)

            purchases_input = input("Purchases: ").strip()
            if purchases_input.lower() == "quit":
                break
            purchases = int(purchases_input)

            margin_input = input("Margin (Enter for auto): ").strip()
            margin = float(margin_input) if margin_input else None

            # Get prediction
            result = predict_single(price, purchases, margin)

            if "error" in result:
                print(f"\n❌ Error: {result['error']}\n")
                continue

            # Display result
            category = result["category"]
            confidence = result["confidence"]
            recommendations = result.get("recommendations", [])

            print("\n" + "-" * 40)
            print(f"Category:   {category}")
            print(f"Confidence: {confidence:.1%}")
            print("\nRecommendations:")
            for rec in recommendations:
                print(f"  • {rec}")
            print("-" * 40 + "\n")

        except ValueError:
            print("Invalid input. Please enter numbers.\n")
        except KeyboardInterrupt:
            break

    print("\nGoodbye!")


def run_sample_demo():
    """Run demo with sample menu items."""
    print("=" * 50)
    print("Sample Menu Items Demo")
    print("=" * 50)

    sample_items = [
        {"name": "The Classic Burger", "price": 110, "purchases": 150},
        {"name": "Premium Steak", "price": 250, "purchases": 30},
        {"name": "Side Salad", "price": 45, "purchases": 200},
        {"name": "Truffle Fries", "price": 85, "purchases": 5},
        {"name": "Kids Menu", "price": 55, "purchases": 8},
        {"name": "House Wine", "price": 75, "purchases": 300},
        {"name": "Lobster Special", "price": 350, "purchases": 2},
        {"name": "Bread Basket", "price": 25, "purchases": 400},
    ]

    print(f"\nAnalyzing {len(sample_items)} sample items...\n")

    results = []
    for item in sample_items:
        result = predict_single(item["price"], item["purchases"])
        if "error" not in result:
            results.append(
                {
                    "Item": item["name"],
                    "Price": item["price"],
                    "Sales": item["purchases"],
                    "Category": result["category"],
                    "Confidence": f"{result['confidence']:.0%}",
                }
            )

    df = pd.DataFrame(results)
    print(df.to_string(index=False))

    print("\n" + "=" * 50)
    print("Category Breakdown:")
    for cat in ["Star", "Plowhorse", "Puzzle", "Dog"]:
        count = (df["Category"] == cat).sum()
        print(f"  {cat}: {count} items")


def main():
    parser = argparse.ArgumentParser(description="Menu Engineering ML Model Demo")
    parser.add_argument("--file", "-f", help="CSV file to process")
    parser.add_argument("--sample", "-s", action="store_true", help="Run sample demo")
    args = parser.parse_args()

    # Check ML service health
    try:
        r = requests.get(f"{ML_SERVICE_URL}/health", timeout=5)
        if r.status_code != 200 or not r.json().get("model_loaded"):
            print("⚠️  ML service not ready. Make sure Docker is running:")
            print("   docker compose up -d")
            return
    except:
        print("❌ Cannot connect to ML service at", ML_SERVICE_URL)
        print("   Make sure Docker is running: docker compose up -d")
        return

    print("✅ ML service is ready!\n")

    if args.file:
        process_csv(args.file)
    elif args.sample:
        run_sample_demo()
    else:
        interactive_mode()


if __name__ == "__main__":
    main()
