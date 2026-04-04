import os
import io
import re
from contextlib import redirect_stdout

import pandas as pd
from cleverminer import cleverminer

# =========================
# PATHS
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", "..", ".."))

input_path = os.path.join(PROJECT_ROOT, "out", "4ft-Miner", "prepared_ai_adoption.csv")

print("INPUT PATH:", input_path)
print("INPUT EXISTS:", os.path.exists(input_path))

# =========================
# LOAD DATA
# =========================
df = pd.read_csv(input_path)

print("=" * 80)
print("DATA LOADED")
print("=" * 80)
print("Shape:", df.shape)
print(df.head())

for col in df.columns:
    df[col] = df[col].astype(str)

# =========================
# RUN CLEVERMINER
# =========================
clm = cleverminer(
    df=df,
    proc='4ftMiner',
    quantifiers={
        'Base': 1650,
        'aad': 0.10
    },
    ante={
        'attributes': [
            {'name': 'industry', 'type': 'subset', 'minlen': 1, 'maxlen': 1},
            {'name': 'company_size', 'type': 'subset', 'minlen': 1, 'maxlen': 1},
            {'name': 'company_age_group', 'type': 'subset', 'minlen': 1, 'maxlen': 1},
            {'name': 'projects_level', 'type': 'seq', 'minlen': 1, 'maxlen': 3},
            {'name': 'training_level', 'type': 'seq', 'minlen': 1, 'maxlen': 3},
            {'name': 'budget_level', 'type': 'seq', 'minlen': 1, 'maxlen': 3},
            {'name': 'maturity_level', 'type': 'seq', 'minlen': 1, 'maxlen': 3},
            {'name': 'automation_level', 'type': 'seq', 'minlen': 1, 'maxlen': 3}
        ],
        'minlen': 1,
        'maxlen': 3,
        'type': 'con'
    },
    succ={
        'attributes': [
            {
                'name': 'ai_adoption_full',
                'type': 'one',
                'value': 'True'
            }
        ],
        'minlen': 1,
        'maxlen': 1,
        'type': 'con'
    }
)

# =========================
# CAPTURE OUTPUT
# =========================
summary_buffer = io.StringIO()
with redirect_stdout(summary_buffer):
    clm.print_summary()
summary_text = summary_buffer.getvalue()

rules_buffer = io.StringIO()
with redirect_stdout(rules_buffer):
    clm.print_rulelist()
rules_text = rules_buffer.getvalue()

print(summary_text)

# =========================
# PARSE RULES
# =========================
rule_pattern = re.compile(
    r'^\s*(\d+)\s+(\d+)\s+([0-9.]+)\s+([+\-]?[0-9.]+)\s+(.*?)\s+\|\s+---\s*$'
)

parsed_rules = []

for line in rules_text.splitlines():
    match = rule_pattern.match(line)
    if match:
        parsed_rules.append({
            "rule_id": int(match.group(1)),
            "base": int(match.group(2)),
            "conf": float(match.group(3)),
            "aad": float(match.group(4)),
            "rule_text": match.group(5).strip()
        })

print("=" * 80)
print("RAW RULES PARSED")
print("=" * 80)
print("Parsed rules:", len(parsed_rules))
print()

# =========================
# REMOVE OBVIOUS USELESS RULES
# =========================
USELESS_PATTERNS = [
    "projects_level(low medium high)",
    "training_level(low medium high)",
    "budget_level(low medium high)",
    "maturity_level(low medium high)",
    "automation_level(low medium high)"
]

def clean_rule_text(rule_text: str) -> str:
    antecedent, consequent = rule_text.split("=>")
    parts = [p.strip() for p in antecedent.split("&")]
    parts = [p for p in parts if p not in USELESS_PATTERNS]
    parts = sorted(parts)
    return f"{' & '.join(parts)} => {consequent.strip()}"

filtered_rules = []
seen = set()

for r in parsed_rules:
    cleaned = clean_rule_text(r["rule_text"])
    if cleaned in seen:
        continue
    seen.add(cleaned)

    new_r = r.copy()
    new_r["cleaned_rule_text"] = cleaned
    filtered_rules.append(new_r)

filtered_rules.sort(key=lambda x: (x["conf"], x["aad"], x["base"]), reverse=True)

print("=" * 80)
print("TOP 10 FILTERED RULES")
print("=" * 80)
for i, r in enumerate(filtered_rules[:10], start=1):
    print(
        f"{i}. BASE={r['base']}, CONF={r['conf']:.3f}, AAD={r['aad']:+.3f} | "
        f"{r['cleaned_rule_text']}"
    )
print()

# =========================
# PICK TOP 3 FOR REPORT
# =========================
report_rules = []
used_signatures = set()

def signature(rule_text: str):
    antecedent = rule_text.split("=>")[0].strip()
    feats = sorted([p.split("(")[0].strip() for p in antecedent.split("&")])
    return tuple(feats)

for r in filtered_rules:
    sig = signature(r["cleaned_rule_text"])
    if sig in used_signatures:
        continue
    used_signatures.add(sig)
    report_rules.append(r)
    if len(report_rules) == 3:
        break

print("=" * 80)
print("TOP 3 RULES FOR REPORT")
print("=" * 80)
for i, r in enumerate(report_rules, start=1):
    print(f"{i}. BASE={r['base']}, CONF={r['conf']:.3f}, AAD={r['aad']:+.3f}")
    print(f"   Rule: {r['cleaned_rule_text']}")
    print()

# =========================
# HUMAN INTERPRETATION
# =========================
def humanize(text: str) -> str:
    mapping = {
        "projects_level(high)": "high number of active AI projects",
        "training_level(high)": "high employee AI training",
        "budget_level(high)": "high AI budget",
        "maturity_level(high)": "high AI maturity",
        "automation_level(high)": "high automation level",
        "company_size(Enterprise)": "enterprise companies",
        "company_size(SME)": "SME companies",
        "company_size(Startup)": "startup companies",
    }
    antecedent = text.split("=>")[0].strip()
    parts = [p.strip() for p in antecedent.split("&")]
    out = [mapping.get(p, p) for p in parts]
    return ", ".join(out)

print("=" * 80)
print("HUMAN-READABLE INTERPRETATION")
print("=" * 80)
for i, r in enumerate(report_rules, start=1):
    print(
        f"{i}. Companies with {humanize(r['cleaned_rule_text'])} "
        f"tend to achieve full AI adoption "
        f"(confidence = {r['conf']:.1%}, base = {r['base']})."
    )
print()

# =========================
# CZECH TEXT FOR REPORT
# =========================
cz_text = (
    "Analýza pomocí 4ft-Miner ukázala, že plná adopce AI souvisí především s kombinací "
    "pokročilejších charakteristik firmy. Mezi nejsilnější pravidla patřily vysoký počet "
    "aktivních AI projektů, vysoká úroveň školení zaměstnanců, vyšší AI rozpočet a vyšší "
    "míra automatizace. Výsledky tedy naznačují, že plná adopce AI se objevuje zejména u firem, "
    "které do AI nejen investují, ale také ji aktivně rozvíjejí prostřednictvím školení, projektů "
    "a praktického nasazení v procesech."
)

print("=" * 80)
print("CZECH INTERPRETATION FOR REPORT")
print("=" * 80)
print(cz_text)
print()