# StoryCoder: Narrative Reformulation for Structured Reasoning in LLM Code Generation

<p align="left">
  <a href="https://arxiv.org/abs/2604.14631"><img src="https://img.shields.io/badge/arXiv-2604.14631-b31b1b.svg" alt="arXiv"></a>
</p>

*Accepted at ACL 2026 Main Conference!* 🎉

## Overview

> **StoryCoder** is a narrative reformulation framework that transforms code generation problems into coherent natural language narratives, guiding LLMs toward more structured reasoning and better algorithmic strategies.
> 
> Existing approaches augment reasoning steps or inject specific structure into how models think, but leave scattered problem conditions unchanged. StoryCoder addresses this by reorganizing task representation itself: converting fragmented, instruction-like problem statements into structured narratives that provide richer contextual structure than simple rephrasings.

Each narrative consists of three components, guided by the selected algorithm and genre:

- **Task Overview**: Presents the coding objective within a narrative frame, integrating scattered conditions into a coherent system.
- **Constraints**: Reframes input ranges, time limits, and rules as natural restrictions in the story.
- **Example Input/Output**: Integrates sample test cases into contextual scenarios, preserving formal coding task requirements within the narrative space.

<p align="center">
  <img src="figures/teaser.png" width="90%">
</p>

## Repository Structure

```plaintext
StoryCoder/
├── run_pipeline.py          # Run the full pipeline (Steps 1 & 2)
├── convert_to_narrative.py  # Step 1: Generate narratives from coding problems
├── split_narratives.py      # Step 2: Split variants into per-variant jsonl files
├── instruction_template.py  # Prompt template for narrative reformulation
└── datasets/
    └── <benchmark>/
        ├── <input_file>     # Input jsonl file
        └── narrative/       # Generated narrative jsonl files
            └── <generator>/
                └── split/   # Per-variant jsonl files
```

## Installation

```bash
pip install google-genai openai anthropic
```

API keys are read from environment variables:

```bash
export OPENAI_API_KEY=...
export ANTHROPIC_API_KEY=...
export GOOGLE_PROJECT_ID=...
export GOOGLE_LOCATION=...
```

## Usage

Place your input jsonl file under `datasets/<benchmark>/`. Then run the full pipeline with a single command:
 
```bash
python run_pipeline.py \
    --benchmark livecodebench \
    --input_file test6.jsonl \
    --generator claude-opus-4-7 \
    --n_variants 5
```
 
**Arguments:**
 
| Argument | Description | Default |
|---|---|---|
| `--benchmark` | Benchmark directory under `datasets/` | required |
| `--input_file` | Input jsonl filename under `<benchmark>/` | required |
| `--generator` | Narrative generator model name (e.g., `gemini-3.1-flash-lite-preview`, `gpt-5.4-mini`, `claude-opus-4-7`) | required |
| `--n_variants` | Number of narrative variants per problem | `5` |
| `--datasets_dir` | Root directory containing all benchmark datasets | `datasets` |
 
### Step 1: Generate Narratives
 
The pipeline reads from:
 
```plaintext
datasets/<benchmark>/<input_file>
```
 
Each sample must contain at least the following fields (same format as LiveCodeBench dataset files):
 
```json
{
  "question_id": "unique_id",
  "question_content": "Problem statement here..."
}
```
 
Generated narratives are saved to:
 
```plaintext
datasets/<benchmark>/narrative/<generator>/<original_file_name>_narratives.jsonl
```
 
A `narratives` field containing `n_variants` narrative strings is appended to each problem:
 
```json
{
  "question_id": "unique_id",
  "question_content": "...",
  "narratives": [
    "- Algorithm Category: Dynamic Programming\n- Narrative Genre: Fantasy Adventure\n- Task Overview: ...",
    "..."
  ]
}
```
 
### Step 2: Split into Per-Variant Files
 
The narrative jsonl from Step 1 is split into one file per variant, saved under:
 
```plaintext
datasets/<benchmark>/narrative/<generator>/split/<original_file_name>_narrative_1.jsonl
...
datasets/<benchmark>/narrative/<generator>/split/<original_file_name>_narrative_N.jsonl
```
 
Each file replaces `question_content` with the corresponding narrative text (with the Algorithm Category and Narrative Genre headers stripped) and drops the `narratives` field, making it directly compatible with the LiveCodeBench evaluation pipeline.
 
### Step 3: Evaluation
 
Each per-variant jsonl file produced in Step 2 can be used directly as the input dataset for the code generation evaluation of LiveCodeBench. No other changes to the evaluation pipeline are needed.

## Acknowledgements
 
This work uses the code generation evaluation pipeline of [LiveCodeBench](https://github.com/LiveCodeBench/LiveCodeBench).

## Citation

If you find this work useful, please cite our paper:

```bibtex
@inproceedings{jang2026storycoder,
  title     = {StoryCoder: Narrative Reformulation for Structured Reasoning in LLM Code Generation},
  author    = {Jang, Geonhui and Han, Dongyoon and Yoo, YoungJoon},
  booktitle = {Proceedings of the 64th Annual Meeting of the Association for Computational Linguistics},
  year      = {2026}
}
```