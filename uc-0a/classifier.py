import pandas as pd
import argparse

URGENT_KEYWORDS = [
    "injury", "child", "school", "hospital",
    "ambulance", "fire", "hazard", "fell", "collapse"
]

CATEGORY_MAP = {
    "pothole": "Pothole",
    "flood": "Flooding",
    "waterlogging": "Flooding",
    "streetlight": "Streetlight",
    "light": "Streetlight",
    "garbage": "Waste",
    "waste": "Waste",
    "noise": "Noise",
    "road": "Road Damage",
    "heritage": "Heritage Damage",
    "heat": "Heat Hazard",
    "drain": "Drain Blockage"
}

def classify_complaint(text):
    text_lower = str(text).lower()

    category = "Other"
    flag = ""

    for keyword, mapped_category in CATEGORY_MAP.items():
        if keyword in text_lower:
            category = mapped_category
            break

    priority = "Standard"

    for keyword in URGENT_KEYWORDS:
        if keyword in text_lower:
            priority = "Urgent"
            break

    if category == "Other":
        flag = "NEEDS_REVIEW"

    reason = f"Detected keywords from complaint: {text}"

    return category, priority, reason, flag


def batch_classify(input_file, output_file):
    df = pd.read_csv(input_file)

    results = df["description"].apply(classify_complaint)

    df[["category", "priority", "reason", "flag"]] = pd.DataFrame(
        results.tolist(),
        index=df.index
    )

    df.to_csv(output_file, index=False)

    print(f"Results saved to {output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)

    args = parser.parse_args()

    batch_classify(args.input, args.output)