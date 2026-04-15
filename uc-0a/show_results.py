import csv, sys

files = sys.argv[1:] if len(sys.argv) > 1 else [
    "results_pune.csv", "results_hyderabad.csv",
    "results_kolkata.csv", "results_ahmedabad.csv"
]

totals = {"clean": 0, "review": 0, "rows": 0}
for target in files:
    try:
        with open(target, encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
    except FileNotFoundError:
        print(f"[SKIP] {target} not found"); continue

    clean  = sum(1 for r in rows if not r.get("flag",""))
    review = len(rows) - clean
    totals["clean"] += clean; totals["review"] += review; totals["rows"] += len(rows)

    print(f"\n{'='*90}")
    print(f" {target}  |  Clean: {clean}/{len(rows)}   NEEDS_REVIEW: {review}/{len(rows)}")
    print(f"{'='*90}")
    print(f"{'Row':<4} {'Category':<16} {'Priority':<9} {'Flag':<13} Description (60 chars)")
    print("-"*90)
    for i, r in enumerate(rows, 1):
        flag = r.get("flag","") or "OK"
        desc = (r.get("description","") or r.get("Description",""))[:60]
        cat  = r.get("category","")
        pri  = r.get("priority","")
        marker = "⚑" if flag == "NEEDS_REVIEW" else " "
        print(f"{marker}{i:<3} {cat:<16} {pri:<9} {flag:<13} {desc}")

print(f"\n{'='*90}")
print(f" OVERALL  |  Clean: {totals['clean']}/{totals['rows']}   NEEDS_REVIEW: {totals['review']}/{totals['rows']}   Accuracy proxy: {totals['clean']/totals['rows']*100:.0f}%")
print(f"{'='*90}")
