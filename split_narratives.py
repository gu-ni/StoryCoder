import os
import json
import re
import argparse


def remove_algorithm_and_genre(text: str) -> str:
    """
    Removes the Algorithm Category and Narrative Genre sections from a narrative.
    Handles variations with/without a leading '-' and with/without ':'.
    The remaining three sections (Task Overview, Constraints, Example Input/Output)
    are returned as the final question content passed to the solver.
    """
    text = re.sub(
        r"(?si)^\s*(-\s*)?Algorithm Category:?\s*.*?(?=\n\s*(-\s*)?Narrative Genre:?\s*|\Z)",
        "",
        text,
        flags=re.MULTILINE,
    )
    text = re.sub(
        r"(?si)^\s*(-\s*)?Narrative Genre:?\s*.*?(?=\n\s*(-\s*)?(Task Overview|Constraints|Example Input/Output)|\Z)",
        "",
        text,
        flags=re.MULTILINE,
    )
    return text.strip()


def run_split(input_path: str, output_dir: str):
    os.makedirs(output_dir, exist_ok=True)

    with open(input_path, "r", encoding="utf-8") as f:
        problems = [json.loads(line) for line in f]

    if not problems or "narratives" not in problems[0]:
        raise ValueError("No narratives found in the input file.")

    num_variants = len(problems[0]["narratives"])
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    # Strip trailing '_narratives' suffix if present
    if base_name.endswith("_narratives"):
        base_name = base_name[: -len("_narratives")]

    print(f"Found {len(problems)} problems, each with {num_variants} narrative variant(s).")

    for variant_idx in range(num_variants):
        output_path = os.path.join(output_dir, f"{base_name}_narrative_{variant_idx + 1}.jsonl")

        with open(output_path, "w", encoding="utf-8") as outfile:
            for problem in problems:
                new_problem = dict(problem)
                new_problem["question_content"] = remove_algorithm_and_genre(
                    new_problem["narratives"][variant_idx]
                )
                new_problem.pop("narratives", None)
                outfile.write(json.dumps(new_problem, ensure_ascii=False) + "\n")

        print(f"  Saved: {output_path}")

    print(f"\nDone. {num_variants} variant file(s) saved to: {output_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Split a multi-variant narrative jsonl file into one jsonl file per variant. "
            "Each output file replaces question_content with the narrative text and is "
            "ready to be used as input for LiveCodeBench evaluation."
        )
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
        "--generator",
        type=str,
        required=True,
        help="LLM generator used for narrative reformulation.",
    )
    parser.add_argument(
        "--input_file",
        type=str,
        required=True,
        help="Input jsonl filename under <benchmark>/narrative/<generator>/ (e.g. 'test6_narratives.jsonl').",
    )
    args = parser.parse_args()

    input_path = os.path.join(args.datasets_dir, args.benchmark, "narrative", args.generator, args.input_file)
    split_dir  = os.path.join(args.datasets_dir, args.benchmark, "narrative", args.generator, "split")
    run_split(input_path, split_dir)