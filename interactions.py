# interactions.py
"""
Simple local medication interaction checker.
Uses medication search results (from india_meds.search_meds)
and a small built-in ruleset (pair -> severity + message).

Severity levels: info / warn / danger
"""

from typing import Tuple, Dict, Optional

# minimal rule set for demo. Keys are lowercase canonical names or salts.
# Use frozenset so order doesn't matter.
INTERACTION_RULES = {
    frozenset(["ciprofloxacin", "tizanidine"]): {
        "severity": "danger",
        "msg": "Ciprofloxacin may greatly increase levels/effects of tizanidine — combination is contraindicated."
    },
    frozenset(["warfarin", "aspirin"]): {
        "severity": "warn",
        "msg": "Warfarin + aspirin increases bleeding risk. Monitor closely and consult physician."
    },
    frozenset(["paracetamol", "alcohol"]): {
        "severity": "info",
        "msg": "Chronic heavy alcohol use can increase liver toxicity risk with paracetamol."
    }
}

def _normalize(name: str) -> str:
    if not name:
        return ""
    return name.strip().lower()

def check_interaction_by_names(a: str, b: str) -> Optional[Dict]:
    """
    Given two medication names (or salts), return an interaction dict or None.
    """
    na = _normalize(a)
    nb = _normalize(b)
    if not na or not nb:
        return None
    key = frozenset([na, nb])
    rule = INTERACTION_RULES.get(key)
    if rule:
        return {"severity": rule["severity"], "message": rule["msg"], "pair": (a, b)}
    return None

def best_match_interaction(med_a: dict, med_b: dict) -> Optional[Dict]:
    """
    Accept medication records (dicts from india_meds.search_meds) and check:
    - try brand/name
    - try salt
    """
    names_to_try = []
    for d in (med_a, med_b):
        if not d:
            names_to_try.append([""])
            continue
        opts = []
        if d.get("name"):
            opts.append(d["name"])
        if d.get("brand"):
            opts.append(d["brand"])
        if d.get("salt"):
            opts.append(d["salt"])
        names_to_try.append(opts)

    # cross-check every combination
    for xa in names_to_try[0]:
        for xb in names_to_try[1]:
            res = check_interaction_by_names(xa, xb)
            if res:
                # include which values matched
                res["matched"] = (xa, xb)
                return res
    return None