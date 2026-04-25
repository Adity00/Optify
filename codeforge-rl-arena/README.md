# CodeForge RL Arena

An OpenEnv-powered reinforcement learning arena for code modification and optimization.

## Structure

- `env/`: OpenEnv environment and sandboxed execution.
- `reward/`: Multi-component reward system (correctness, efficiency, cleanliness).
- `training/`: GRPO training loop and dataset utilities.
- `tasks/`: Multi-level coding challenges.
- `demo/`: Gradio-based visualization and before/after comparisons.

## Installation

```bash
pip install -r requirements.txt
```

## Running the Arena

```bash
python training/train.py
```
