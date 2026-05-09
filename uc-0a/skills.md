skills:
  - name: classify_complaint
    input:
      - complaint_text
    output:
      - category
      - priority
      - reason
      - flag

  - name: batch_classify
    input:
      - input_csv
    output:
      - output_csv