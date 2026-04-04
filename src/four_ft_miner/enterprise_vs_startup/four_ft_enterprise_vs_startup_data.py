import os
import io
import re
import textwrap
from contextlib import redirect_stdout

import pandas as pd
from cleverminer import cleverminer

# =========================
# PATHS
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", "..", ".."))

INPUT_PATH = os.path.join(PROJECT_ROOT, "out", "four_ft_miner", "prepared_enterprise_vs_startup.csv")

print("INPUT PATH:", INPUT_PATH)
print("INPUT EXISTS:", os.path.exists(INPUT_PATH))

# =========================
# LOAD DATA
# =========================
df = pd.read_csv(INPUT_PATH)

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
    proc="4ftMiner",
    quantifiers={
        "Base": 4000,
        "aad": 0.08
    },
    ante={
        "attributes": [
            {"name": "ai_adoption_stage", "type": "subset", "minlen": 1, "maxlen": 1},
            {"name": "data_privacy_level", "type": "subset", "minlen": 1, "maxlen": 1},
            {"name": "ai_ethics_committee", "type": "subset", "minlen": 1, "maxlen": 1},
            {"name": "experience_level", "type": "seq", "minlen": 1, "maxlen": 3},
            {"name": "tools_used_level", "type": "seq", "minlen": 1, "maxlen": 3},
            {"name": "projects_level", "type": "seq", "minlen": 1, "maxlen": 3},
            {"name": "training_level", "type": "seq", "minlen": 1, "maxlen": 3},
            {"name": "budget_level", "type": "seq", "minlen": 1, "maxlen": 3},
            {"name": "maturity_level", "type": "seq", "minlen": 1, "maxlen": 3},
            {"name": "compliance_level", "type": "seq", "minlen": 1, "maxlen": 3},
            {"name": "risk_level", "type": "seq", "minlen": 1, "maxlen": 3},
            {"name": "automation_level", "type": "seq", "minlen": 1, "maxlen": 3},
        ],
        "minlen": 1,
        "maxlen": 3,
        "type": "con"
    },
    succ={
        "attributes": [
            {
                "name": "is_enterprise",
                "type": "one",
                "value": "True"
            }
        ],
        "minlen": 1,
        "maxlen": 1,
        "type": "con"
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
# CLEAN RULES
# =========================
USELESS_PATTERNS = [
    "experience_level(high low medium)",
    "tools_used_level(high low medium)",
    "projects_level(high low medium)",
    "training_level(high low medium)",
    "budget_level(high low medium)",
    "maturity_level(high low medium)",
    "compliance_level(high low medium)",
    "risk_level(high low medium)",
    "automation_level(high low medium)"
]

def clean_rule_text(rule_text: str) -> str:
    antecedent, consequent = rule_text.split("=>")
    parts = [p.strip() for p in antecedent.split("&")]
    parts = [p for p in parts if p not in USELESS_PATTERNS]
    parts = sorted(parts)
    if not parts:
        return ""
    return f"{' & '.join(parts)} => {consequent.strip()}"

filtered_rules = []
seen = set()

for r in parsed_rules:
    cleaned = clean_rule_text(r["rule_text"])
    if not cleaned:
        continue
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
# PICK TOP 3 REPORT RULES
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
# HUMAN-READABLE INTERPRETATION
# =========================
def humanize(text: str) -> str:
    mapping = {
        "ai_adoption_stage(partial)": "partial AI adoption stage",
        "ai_adoption_stage(pilot)": "pilot AI adoption stage",
        "ai_adoption_stage(full)": "full AI adoption stage",
        "data_privacy_level(High)": "high data privacy level",
        "data_privacy_level(Medium)": "medium data privacy level",
        "data_privacy_level(Low)": "low data privacy level",
        "ai_ethics_committee(Yes)": "presence of an AI ethics committee",
        "ai_ethics_committee(No)": "absence of an AI ethics committee",
        "experience_level(high)": "high AI usage experience",
        "tools_used_level(high)": "high number of AI tools used",
        "projects_level(high)": "high number of active AI projects",
        "training_level(high)": "high employee AI training",
        "budget_level(high)": "high AI budget",
        "maturity_level(high)": "high AI maturity",
        "compliance_level(high)": "high regulatory compliance",
        "risk_level(high)": "high AI risk management level",
        "automation_level(high)": "high automation level",
    }

    antecedent = text.split("=>")[0].strip()
    parts = [p.strip() for p in antecedent.split("&")]
    out = [mapping.get(p, p) for p in parts]
    return ", ".join(out)

print("=" * 80)
print("HUMAN-READABLE INTERPRETATION")
print("=" * 80)

if not report_rules:
    print("No strong report rules were found.")
else:
    for i, r in enumerate(report_rules, start=1):
        print(
            f"{i}. Companies with {humanize(r['cleaned_rule_text'])} "
            f"are more likely to be Enterprise rather than Startup "
            f"(confidence = {r['conf']:.1%}, base = {r['base']})."
        )
print()

# =========================
# CZECH INTERPRETATION
# =========================

def print_wrapped(text, width=100):
    print("\n".join(textwrap.wrap(text, width=width)))
cz_text = (
    "Analýza pomocí four_ft_miner ukázala, že podniky Enterprise a Startup se liší "
    "v několika charakteristikách souvisejících s adopcí AI. Nejsilnější pravidla "
    "ukazují, že firmy typu Enterprise častěji vykazují přítomnost AI etické komise, "
    "vyšší rozpočet na AI a vyšší počet aktivních AI projektů. Další silná pravidla "
    "naznačují, že podniky Enterprise mají také častěji vyšší úroveň řízení AI rizik "
    "a vyšší úroveň školení zaměstnanců v oblasti AI. Výsledky tedy naznačují, že "
    "firmy typu Enterprise přistupují k adopci AI systematičtěji, investují více "
    "prostředků do jejího rozvoje a častěji zavádějí formální mechanismy řízení a kontroly."
)

print("=" * 80)
print("CZECH INTERPRETATION FOR REPORT")
print("=" * 80)
print_wrapped(cz_text, width=100)
print()