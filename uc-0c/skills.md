skills:
  - name: load_dataset
    input:
      - csv_file
    output:
      - validated_dataset
      - null_report

  - name: compute_growth
    input:
      - ward
      - category
      - growth_type
    output:
      - growth_table