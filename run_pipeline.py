import os
import argparse
from convert_to_narrative import init_client, run_convert
from split_narratives import run_split

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Run the full StoryCoder pipeline: generate narratives from coding problems "
            "and split them into per-variant jsonl files ready for LiveCodeBench evaluation."
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
        "--input_file",
        type=str,
        required=True,
        help="Input jsonl filename under <benchmark>/ (e.g. 'test6.jsonl').",
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

    base_name      = os.path.splitext(args.input_file)[0]
    input_path     = os.path.join(args.datasets_dir, args.benchmark, args.input_file)
    narrative_path = os.path.join(args.datasets_dir, args.benchmark, "narrative", args.generator, f"{base_name}_narratives.jsonl")
    split_dir      = os.path.join(args.datasets_dir, args.benchmark, "narrative", args.generator, "split")

    client, backend = init_client(args.generator)

    print("=" * 60)
    print(f"Step 1: Generating narratives → {narrative_path}")
    print("=" * 60)
    run_convert(client, backend, args.generator, input_path, narrative_path, args.n_variants)

    print("\n" + "=" * 60)
    print(f"Step 2: Splitting narratives → {split_dir}/")
    print("=" * 60)
    run_split(narrative_path, split_dir)