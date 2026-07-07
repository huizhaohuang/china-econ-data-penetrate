"""Load the hand-edited explanation layer (content/indicators.yaml)."""

from __future__ import annotations

from pathlib import Path

import streamlit as st
import yaml

ROOT = Path(__file__).resolve().parents[2]
INDICATORS_YAML = ROOT / "content" / "indicators.yaml"


@st.cache_data(show_spinner=False)
def _read_yaml(path: str, mtime: float) -> dict:
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_content() -> dict:
    """Returns {'blocks': {...}, 'indicators': {...}} with blocks usable
    in declared order via ordered_blocks()."""
    if not INDICATORS_YAML.exists():
        return {"blocks": {}, "indicators": {}}
    return _read_yaml(str(INDICATORS_YAML), INDICATORS_YAML.stat().st_mtime)


def ordered_blocks(content: dict) -> list[tuple[str, dict]]:
    blocks = content.get("blocks", {})
    return sorted(blocks.items(), key=lambda kv: kv[1].get("order", 99))


def indicators_in_block(content: dict, block_id: str) -> list[tuple[str, dict]]:
    return [
        (ind_id, spec)
        for ind_id, spec in content.get("indicators", {}).items()
        if spec.get("block") == block_id
    ]
