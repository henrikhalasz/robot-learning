# robot-learning

Learning robot learning by building it, on two SO-101 arms with wrist and scene cameras.

- `builds/`: one folder per build, each with the command that reproduces it and what it showed.
- `experiments/`: measured results. Each README holds the prediction, written before the run,
  then the numbers with their intervals.
- `src/robot_learning/`: the one package all builds and experiments share; `scripts/` are thin
  command-line entry points into it.
- `outputs/`: where runs write by default (git-ignored). Every output saves its arguments and the
  git commit that produced it.

## Setup

```bash
uv sync               # Python 3.12 environment pinned by uv.lock
uv run pytest         # tests
```

Started October 2026. The first builds are on their way.
