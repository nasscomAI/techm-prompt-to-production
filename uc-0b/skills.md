retrieve_policy: 
  - name: retrieve_policy 
  - description: Loads a policy text file and parses it into a structured dictionary of numbered sections. 
  - input: string (file path to a .txt policy document) 
  - output: object (dictionary mapping clause numbers to their text content) 
  - error_handling: Returns an error if the file is missing, empty, or lacks standard numbered clause formatting; flags ambiguous text that prevents reliable section mapping.

summarize_policy: 
  - name: summarize_policy 
  - description: Produces a compliant summary of policy sections that preserves all clauses and multi-condition obligations without adding external information. 
  - input: object (structured sections mapping clause numbers to text) 
  - output: string (text summary containing all clauses, preserved conditions, and flags for verbatim quotes) 
  - error_handling: Flags a failure if any of the 10 core clauses are omitted, if multi-approver conditions are simplified, or if scope bleed is detected; quotes clauses verbatim if summarization risks meaning loss.