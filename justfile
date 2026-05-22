default:
    just --list

pre-commit:
    uv run prek run --all-files

generate:
    uv run --script dev_scripts/write_cases.py
    uv run --script dev_scripts/path_forms.py
