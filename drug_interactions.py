# drug_interactions.py
"""
Simple local drug-interaction checker.
You can replace the DEFAULT_INTERACTIONS with a larger JSON file later.
"""

import json
import os
from typing import List, Dict, Tuple, Optional

# Optionally load from interactions.json if present, otherwise use default table.
DEFAULT_INTERACTIONS = {
    # keys are lowercase drug names (single token or common name).
    # pair (a,b) maps to a dict with severity and description.
    # pairs are symmetric; we normalize when checking.
    ("aspirin", "warfarin"): {"severity": "high", "desc": "Increased bleeding risk."},
    ("atorvastatin", "clarithromycin"): {"severity": "high", "desc": "Increased statin levels -> muscle/liver risk."},
    ("metformin", "contrast_dye"): {"severity": "moderate", "desc": "Contrast dye may cause lactic acidosis risk."},
    ("lisinopril", "spironolactone"): {"severity": "moderate", "desc": "Hyperkalemia risk when combined."},
    ("ibuprofen", "lisinopril"): {"severity": "moderate", "desc": "NSAIDs can reduce antihypertensive effect and harm kidneys."},
    # example mild interactions
    ("st_johns_wort", "sertraline"): {"severity": "mild", "desc": "Serotonergic interactions possible."},
}

def load_interactions_from_json(path: str) -> Dict[Tuple[str,str], Dict]:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # expect data format: list of {"a": "aspirin", "b": "warfarin", "severity": "high", "desc": "..."}
        out = {}
        for item in data:
            a = item.get("a", "").strip().lower()
            b = item.get("b", "").strip().lower()
            if not a or not b:
                continue
            out[(a,b)] = {"severity": item.get("severity","moderate"), "desc": item.get("desc","")}
        return out
    except Exception:
        return {}

# Build combined interactions: default + file (file overrides default)
def build_interaction_map(json_path: Optional[str]=None) -> Dict[Tuple[str,str], Dict]:
    m = {}
    # normalize keys
    for (a,b), v in DEFAULT_INTERACTIONS.items():
        m[(a.lower(), b.lower())] = v
        m[(b.lower(), a.lower())] = v
    if json_path:
        j = load_interactions_from_json(json_path)
        for (a,b),v in j.items():
            m[(a.lower(), b.lower())] = v
            m[(b.lower(), a.lower())] = v
    return m

# Build default map on import (search for interactions.json in CWD)
INTERACTIONS = build_interaction_map(json_path="interactions.json")

def normalize_name(name: str) -> str:
    """Simple normalizer: lower, strip, remove common punctuation."""
    if not name:
        return ""
    s = name.lower().strip()
    # remove punctuation commonly typed (keep alphanumerics and spaces and underscore)
    import re
    s = re.sub(r"[^a-z0-9 _]", " ", s)
    # collapse spaces
    s = " ".join(s.split())
    # as an enhancement, you can map synonyms here (e.g., "vit d" -> "vitamin d")
    return s

def check_pair(a: str, b: str) -> Optional[Dict]:
    """Return interaction dict if found for pair (a,b), otherwise None."""
    if not a or not b:
        return None
    a_n = normalize_name(a)
    b_n = normalize_name(b)
    # direct exact lookup
    if (a_n, b_n) in INTERACTIONS:
        return INTERACTIONS[(a_n, b_n)]
    if (b_n, a_n) in INTERACTIONS:
        return INTERACTIONS[(b_n, a_n)]
    # try token-level lookups: check any token combinations
    a_tokens = a_n.split()
    b_tokens = b_n.split()
    for at in a_tokens:
        for bt in b_tokens:
            if (at, bt) in INTERACTIONS:
                return INTERACTIONS[(at, bt)]
            if (bt, at) in INTERACTIONS:
                return INTERACTIONS[(bt, at)]
    return None

def scan_list(med_names: List[str]) -> List[Dict]:
    """
    Check every pair in med_names. Return list of dicts:
    {"a": nameA, "b": nameB, "severity": ..., "desc": ...}
    """
    out = []
    n = len(med_names)
    for i in range(n):
        for j in range(i+1, n):
            a = med_names[i]
            b = med_names[j]
            found = check_pair(a, b)
            if found:
                out.append({"a": a, "b": b, "severity": found.get("severity","moderate"), "desc": found.get("desc","")})
    return out