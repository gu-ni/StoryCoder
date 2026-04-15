import os
import json
import argparse
from instruction_template import INSTRUCTION_THREE_COMPONENTS_ALGORITHM

from google import genai
from google.genai.types import GenerateContentConfigDict
from openai import OpenAI
import anthropic


# ====================
# Load already-processed question IDs from an existing output file
# ====================
def load_existing_question_ids(path):
    if not os.path.exists(path):
        return set()
    existing_ids = set()
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                obj = json.loads(line)
                qid = obj.get("question_id")
                if qid:
                    existing_ids.add(qid)
            except Exception:
                continue
    return existing_ids


# --------------------
# Gemini
# --------------------
def call_gemini(client, prompt):
    response = client.models.generate_content(
        model="gemini-3.1-flash-lite-preview",
        contents=prompt,
        config=GenerateContentConfigDict(
            temperature=1.0,
            max_output_tokens=8192,
        ),
    )
    if response and response.candidates:
        return response.candidates[0].content.parts[0].text.strip()
    return ""


# --------------------
# ChatGPT (OpenAI)
# --------------------
def call_gpt(client, prompt):
    response = client.responses.create(
        model="gpt-5.4-mini-2026-03-17",
        instructions="You are an imaginative storyteller who follows instructions well.",
        input=[{"role": "user", "content": prompt}],
        reasoning={"effort": "medium"},
        max_output_tokens=8192,
    )
    return response.output_text.strip()


# --------------------
# Claude (Anthropic)
# --------------------
def call_claude(client, prompt):
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8192,
        temperature=1.0,
        messages=[
            {"role": "user", "content": prompt}
        ],
    )
    content = "\n".join(
        block.text for block in response.content if hasattr(block, "text")
    )
    return content.strip()


# ====================
# Main
# ====================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert coding benchmark problems into narrative stories using an LLM backend."
    )
    parser.add_argument(
        "--backend",
        type=str,
        required=True,
        choices=["gemini", "chatgpt", "claude"],
        help="LLM backend to use for narrative generation.",
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to the input JSONL file containing coding problems.",
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Path to the output JSONL file where narrative results will be saved.",
    )
    parser.add_argument(
        "--n_variants",
        type=int,
        default=5,
        help="Number of narrative variants to generate per problem.",
    )
    args = parser.parse_args()

    backend = args.backend
    N_VARIANTS = args.n_variants
    input_path = args.input
    output_path = args.output

    # --- Initialize API client ---
    if backend == "gemini":
        client = genai.Client(
            vertexai=True,
            project=os.getenv("GOOGLE_PROJECT_ID"),
            location=os.getenv("GOOGLE_LOCATION"),
        )
    elif backend == "chatgpt":
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    elif backend == "claude":
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    else:
        raise ValueError(f"Unsupported backend: {backend}")

    # --- Prepare output directory ---
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    existing_ids = load_existing_question_ids(output_path)

    with open(input_path, "r", encoding="utf-8") as infile, \
         open(output_path, "a", encoding="utf-8") as outfile:

        for i, line in enumerate(infile):
            try:
                problem = json.loads(line)
                qid = problem.get("question_id")
                print(f"\n[{i}] Starting problem (qid={qid})...")

                if qid in existing_ids:
                    print(f"  Skipping already-processed qid: {qid}")
                    continue

                input_prompt = INSTRUCTION_THREE_COMPONENTS_ALGORITHM + problem["question_content"]

                narratives = []
                for v in range(N_VARIANTS):
                    if backend == "gemini":
                        new_content = call_gemini(client, input_prompt)
                    elif backend == "chatgpt":
                        new_content = call_gpt(client, input_prompt)
                    elif backend == "claude":
                        new_content = call_claude(client, input_prompt)

                    print(f"\n  [Variant {v+1}] --- {backend.upper()} Response ---\n")
                    print(new_content)
                    print("\n" + "-" * 60 + "\n")

                    if new_content:
                        narratives.append(new_content)

                problem["narratives"] = narratives
                outfile.write(json.dumps(problem, ensure_ascii=False) + "\n")
                outfile.flush()
                existing_ids.add(qid)

                print(f"  Done: problem {i} (qid={qid}), {len(narratives)} variant(s) generated.")

            except Exception as e:
                print(f"[Error] Problem idx={i} qid={qid}: {e}")
                continue

    print(f"\n[Done] Results saved to: {output_path}")
