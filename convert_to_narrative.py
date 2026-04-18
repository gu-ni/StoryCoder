import os
import json
import argparse
from instruction_template import INSTRUCTION_THREE_COMPONENTS_ALGORITHM

from google import genai
from google.genai.types import GenerateContentConfigDict
from openai import OpenAI
import anthropic


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


def call_gemini(client, prompt, model):
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=GenerateContentConfigDict(
            temperature=1.0,
            max_output_tokens=8192,
        ),
    )
    if response and response.candidates:
        return response.candidates[0].content.parts[0].text.strip()
    return ""


def call_gpt(client, prompt, model):
    response = client.responses.create(
        model=model,
        instructions="You are an imaginative storyteller who follows instructions well.",
        input=[{"role": "user", "content": prompt}],
        reasoning={"effort": "medium"},
        max_output_tokens=8192,
    )
    return response.output_text.strip()


def call_claude(client, prompt, model):
    response = client.messages.create(
        model=model,
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


BACKENDS = {
    "gemini": {
        "client": lambda: genai.Client(
            vertexai=True,
            project=os.getenv("GOOGLE_PROJECT_ID"),
            location=os.getenv("GOOGLE_LOCATION"),
        ),
        "call": call_gemini,
    },
    "gpt": {
        "client": lambda: OpenAI(api_key=os.getenv("OPENAI_API_KEY"), max_retries=5),
        "call": call_gpt,
    },
    "claude": {
        "client": lambda: anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"), max_retries=5),
        "call": call_claude,
    },
}


def get_backend(generator: str) -> str:
    for prefix in BACKENDS:
        if generator.startswith(prefix):
            return prefix
    raise ValueError(f"Unsupported generator: {generator}")


def init_client(generator: str):
    backend = get_backend(generator)
    return BACKENDS[backend]["client"](), backend


def run_convert(client, backend: str, generator: str, input_path: str, output_path: str, n_variants: int):
    
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    # Skip already-processed questions to avoid redundant API calls
    existing_ids = load_existing_question_ids(output_path)
    
    model_call = BACKENDS[backend]["call"]
    with open(input_path, "r", encoding="utf-8") as infile, \
         open(output_path, "a", encoding="utf-8") as outfile:

        for i, line in enumerate(infile):
            qid = None
            try:
                problem = json.loads(line)
                qid = problem.get("question_id")
                print(f"\n[{i}] Starting problem (qid={qid})...")

                if qid in existing_ids:
                    print(f"  Skipping already-processed qid: {qid}")
                    continue

                input_prompt = INSTRUCTION_THREE_COMPONENTS_ALGORITHM + problem["question_content"]

                narratives = []
                for v in range(n_variants):
                    new_content = model_call(client, input_prompt, generator)

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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert coding benchmark problems into narrative stories using an LLM generator."
    )
    parser.add_argument(
        "--datasets_dir",
        type=str,
        default="datasets",
        help="Root directory containing all benchmark datasets. Defaults to 'datasets/'.",
    )
    parser.add_argument(
        "--benchmark",
        type=str,
        required=True,
        help="Benchmark directory under <datasets_dir>/ (e.g. 'livecodebench').",
    )
    parser.add_argument(
        "--input_file",
        type=str,
        required=True,
        help="Input jsonl filename under <benchmark>/ (e.g. 'livecodebench_v6.jsonl').",
    )
    parser.add_argument(
        "--generator",
        type=str,
        required=True,
        help="LLM generator to use for narrative reformulation.",
    )
    parser.add_argument(
        "--n_variants",
        type=int,
        default=5,
        help="Number of narrative variants to generate per problem.",
    )
    args = parser.parse_args()

    base_name   = os.path.splitext(args.input_file)[0]
    input_path  = os.path.join(args.datasets_dir, args.benchmark, args.input_file)
    output_path = os.path.join(args.datasets_dir, args.benchmark, "narrative", args.generator, f"{base_name}_narratives.jsonl")
    client, backend = init_client(args.generator)
    run_convert(client, backend, args.generator, input_path, output_path, args.n_variants)