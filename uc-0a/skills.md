skills:
  - name: classify_complaint
    description: Classifies a single citizen complaint to determine its category, priority, reason, and flag.
    input: A single complaint row containing the text description.
    output: A structured object with fields 'category', 'priority', 'reason', and 'flag'.
    error_handling: If the complaint cannot be clearly classified, output category as 'Other' and set flag to 'NEEDS_REVIEW'.

  - name: batch_classify
    description: Reads an input CSV of complaints, applies classify_complaint to each row, and writes the results to an output CSV.
    input: File path to the input CSV.(example D:\techm-prompt-to-production\data\city-test-files\test_pune.csv
    output: File path to the generated output CSV containing the classification results.(example results_pune.csv)
    error_handling: If a row fails to process or is malformed, skip the row or output default 'Other'/'NEEDS_REVIEW' values to ensure the batch process completes without crashing.
