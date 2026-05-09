skills:
  - name: retrieve_policy
    input:
      - policy_txt_file
    output:
      - structured_policy_sections

  - name: summarize_policy
    input:
      - structured_sections
    output:
      - compliant_summary