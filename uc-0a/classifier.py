"""
UC-0A — Complaint Classifier
Delegates classification to uc-0a.app while preserving the README run command interface.
"""
from app import batch_classify, classify_complaint

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="UC-0A Complaint Classifier")
    parser.add_argument("--input", required=True, help="Path to test_[techm].csv")
    parser.add_argument("--output", required=True, help="Path to write results CSV")
    args = parser.parse_args()
    batch_classify(args.input, args.output)
    print(f"Done. Results written to {args.output}")
