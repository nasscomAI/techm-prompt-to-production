"""
UC-0B app.py — Summary That Changes Meaning
Build this using the RICE + agents.md + skills.md + CRAFT workflow.
See README.md for run command and expected behaviour.
"""

import argparse
import os
import sys

def build_sys_prompt(agents_md, skills_md):
    """Constructs the system prompt with RICE rules and available skills."""
    return f"""
--- AGENT CONFIGURATION ---
{agents_md}

--- AVAILABLE SKILLS ---
{skills_md}

You must strictly adhere to the agent configuration above.
Act as the 'retrieve_policy' and 'summarize_policy' skills sequentially:
1. First, parse the provided policy text and ensure you map out all critical clauses internally.
2. Second, apply the strict summary rules enforcing all conditions and combinations defined in agents.md.
Produce ONLY the final output summary, without any conversational filler or preambles.
"""

def main():
    parser = argparse.ArgumentParser(description="Strict Policy Summarizer")
    parser.add_argument("--input", required=True, help="Path to the input policy document")
    parser.add_argument("--output", required=True, help="Path to write the compliant summary")
    args = parser.parse_args()

    # Load the rule documents from the current working directory
    try:
        with open("agents.md", "r", encoding="utf-8") as f:
            agents_md = f.read()
        with open("skills.md", "r", encoding="utf-8") as f:
            skills_md = f.read()
    except FileNotFoundError as e:
        print(f"Error reading configuration files: {e}")
        sys.exit(1)

    # Load the target policy document
    try:
        with open(args.input, "r", encoding="utf-8") as f:
            policy_doc = f.read()
    except FileNotFoundError as e:
        print(f"Error reading input policy doc: {e}")
        sys.exit(1)
        
    print(f"Successfully loaded {args.input}")
    print("Synthesizing prompt rules via agents.md and skills.md...")

    # Optional: We will use google.genai for generation. The user should have it installed.
    try:
        from google import genai
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is missing.")
            
        client = genai.Client(api_key=api_key)
        
        system_instruction = build_sys_prompt(agents_md, skills_md)
        prompt = f"--- POLICY DOCUMENT TO SUMMARIZE ---\n{policy_doc}"
        
        print("Calling LLM (gemini-2.5-pro)...")
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.0  # Zero temperature for strictly deterministic and compliant outputs
            )
        )
        summary = response.text
        
    except ImportError:
        print("WARNING: google-genai is not installed. To run the full LLM pipeline, run:")
        print("pip install google-genai")
        print("\nFallback: Writing the generated prompt directly instead of LLM summary output...")
        summary = build_sys_prompt(agents_md, skills_md) + "\n\n--- POLICY DOCUMENT ---\n" + policy_doc
    except ValueError as ve:
        print(f"WARNING: {ve}")
        print("Fallback: Writing the generated prompt directly instead of LLM summary...")
        summary = build_sys_prompt(agents_md, skills_md) + "\n\n--- POLICY DOCUMENT ---\n" + policy_doc
    except Exception as e:
        print(f"Error generating content via LLM: {e}")
        sys.exit(1)

    # Save output summary
    try:
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(summary)
        print(f"Summary written to: {args.output}")
    except OSError as e:
        print(f"Error writing to output file {args.output}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
