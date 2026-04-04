import pandas as pd
from pathlib import Path
import re
import io
import textwrap
from contextlib import redirect_stdout
from cleverminer import cleverminer

# ===============================
# SETTINGS
# ===============================
BASE_DIR = Path(__file__).resolve().parents[3]

FILE_PATH = BASE_DIR / "out" / "4ft-Miner" / "high_productivity_4ft.csv"

TOP_N_GENERAL = 10          # How many normal rules should I show
TOP_N_REPORT = 3            # How many best rules to suggest for a report
MIN_BASE_FOR_REPORT = 12000 # cut off rules that are too narrow
EXCLUDE_INDUSTRY_RULES_FOR_REPORT = True  # Use general rules for the report, not sector-specific ones.

# ===============================
# LOAD DATA
# ===============================

df = pd.read_csv(FILE_PATH)

print("=" * 80)
print("DATA LOADED")
print("=" * 80)
print("Shape:", df.shape)
print(df.head())
print()

# Just in case, we bring everything to the lines
for col in df.columns:
    df[col] = df[col].astype(str)

# ===============================
# RUN CLEVERMINER
# ===============================

print("=" * 80)
print("RUNNING 4FT-MINER")
print("=" * 80)

clm = cleverminer(
    df=df,
    proc='4ftMiner',
    quantifiers={
        'Base': 5000,
        'aad': 0.15
    },
    ante={
        'attributes': [
            {'name': 'industry', 'type': 'subset', 'minlen': 1, 'maxlen': 1},
            {'name': 'company_size', 'type': 'subset', 'minlen': 1, 'maxlen': 1},
            {'name': 'ai_adoption_stage', 'type': 'subset', 'minlen': 1, 'maxlen': 1},
            {'name': 'ai_maturity', 'type': 'seq', 'minlen': 1, 'maxlen': 3},
            {'name': 'training_level', 'type': 'seq', 'minlen': 1, 'maxlen': 3},
            {'name': 'projects_level', 'type': 'seq', 'minlen': 1, 'maxlen': 3},
            {'name': 'budget_level', 'type': 'seq', 'minlen': 1, 'maxlen': 3},
            {'name': 'automation_level', 'type': 'seq', 'minlen': 1, 'maxlen': 3}
        ],
        'minlen': 1,
        'maxlen': 3,
        'type': 'con'
    },
    succ={
        'attributes': [
            {
                'name': 'high_productivity',
                'type': 'one',
                'value': 'True'
            }
        ],
        'minlen': 1,
        'maxlen': 1,
        'type': 'con'
    }
)

# ===============================
# CAPTURE OUTPUT
# ===============================

summary_buffer = io.StringIO()
with redirect_stdout(summary_buffer):
    clm.print_summary()
summary_text = summary_buffer.getvalue()

rules_buffer = io.StringIO()
with redirect_stdout(rules_buffer):
    clm.print_rulelist()
rules_text = rules_buffer.getvalue()

print(summary_text)

# ===============================
# PARSE RULES
# ===============================

rule_pattern = re.compile(
    r'^\s*(\d+)\s+(\d+)\s+([0-9.]+)\s+([+\-]?[0-9.]+)\s+(.*?)\s+\|\s+---\s*$'
)

parsed_rules = []

for line in rules_text.splitlines():
    match = rule_pattern.match(line)
    if match:
        rule_id = int(match.group(1))
        base = int(match.group(2))
        conf = float(match.group(3))
        aad = float(match.group(4))
        rule_text = match.group(5).strip()

        if "=>" not in rule_text:
            continue

        antecedent, consequent = rule_text.split("=>", 1)
        antecedent = antecedent.strip()
        consequent = consequent.strip()

        parsed_rules.append({
            "rule_id": rule_id,
            "base": base,
            "conf": conf,
            "aad": aad,
            "antecedent": antecedent,
            "consequent": consequent,
            "rule_text": rule_text
        })

print("=" * 80)
print("RAW RULES PARSED")
print("=" * 80)
print("Parsed rules:", len(parsed_rules))
print()

# ===============================
# FILTER USELESS / REDUNDANT RULES
# ===============================

USELESS_PATTERNS = [
    "ai_maturity(high low medium)",
    "training_level(high low medium)",
    "projects_level(high low medium)",
    "budget_level(high low medium)",
    "automation_level(high low medium)"
]

def clean_antecedent(antecedent: str) -> str:
    parts = [p.strip() for p in antecedent.split("&")]
    cleaned_parts = []

    for p in parts:
        if p in USELESS_PATTERNS:
            continue
        cleaned_parts.append(p)

    # sorting for normal deduplication
    cleaned_parts = sorted(cleaned_parts)
    return " & ".join(cleaned_parts)

filtered_rules = []

seen = set()

for rule in parsed_rules:
    cleaned = clean_antecedent(rule["antecedent"])

    # if there is nothing left after cleaning, skip
    if not cleaned:
        continue

    # the key of deduplication by meaning
    key = (cleaned, rule["consequent"])

    # if there was already such a meaning, skip the double
    if key in seen:
        continue
    seen.add(key)

    new_rule = rule.copy()
    new_rule["cleaned_antecedent"] = cleaned
    new_rule["cleaned_rule_text"] = f"{cleaned} => {rule['consequent']}"
    filtered_rules.append(new_rule)

print("=" * 80)
print("FILTERED RULES")
print("=" * 80)
print("After removing obvious duplicates/useless rules:", len(filtered_rules))
print()

# ===============================
# SORT RULES
# ===============================

# First by confidence, then by aad, then by base
filtered_rules.sort(
    key=lambda x: (x["conf"], x["aad"], x["base"]),
    reverse=True
)

# ===============================
# PRINT TOP GENERAL RULES
# ===============================

print("=" * 80)
print(f"TOP {TOP_N_GENERAL} FILTERED RULES")
print("=" * 80)

for i, rule in enumerate(filtered_rules[:TOP_N_GENERAL], start=1):
    print(
        f"{i}. BASE={rule['base']}, CONF={rule['conf']:.3f}, AAD={rule['aad']:+.3f} | "
        f"{rule['cleaned_rule_text']}"
    )

print()

# ===============================
# SELECT RULES FOR REPORT
# ===============================

report_candidates = []

for rule in filtered_rules:
    antecedent = rule["cleaned_antecedent"]

    if EXCLUDE_INDUSTRY_RULES_FOR_REPORT and "industry(" in antecedent:
        continue

    if rule["base"] < MIN_BASE_FOR_REPORT:
        continue

    report_candidates.append(rule)

# Additional logic: we want a variety of rules, not 3 almost identical ones.
selected_for_report = []
used_main_features = set()

def extract_features(antecedent: str):
    features = []
    parts = [p.strip() for p in antecedent.split("&")]
    for p in parts:
        feat = p.split("(")[0].strip()
        features.append(feat)
    return tuple(sorted(features))

for rule in report_candidates:
    feature_signature = extract_features(rule["cleaned_antecedent"])

    if feature_signature in used_main_features:
        continue

    selected_for_report.append(rule)
    used_main_features.add(feature_signature)

    if len(selected_for_report) == TOP_N_REPORT:
        break

print("=" * 80)
print(f"TOP {TOP_N_REPORT} RULES FOR REPORT")
print("=" * 80)

for i, rule in enumerate(selected_for_report, start=1):
    print(
        f"{i}. BASE={rule['base']}, CONF={rule['conf']:.3f}, AAD={rule['aad']:+.3f}"
    )
    print(f"   Rule: {rule['cleaned_rule_text']}")
    print()

# ===============================
# HUMAN-READABLE EXPLANATION
# ===============================

def humanize_condition(cond: str) -> str:
    replacements = {
        "ai_adoption_stage(partial)": "partial AI adoption stage",
        "ai_maturity(high)": "high AI maturity",
        "ai_maturity(high low)": "high or low AI maturity",
        "training_level(high)": "high employee AI training",
        "training_level(high low)": "high or low employee AI training",
        "projects_level(high)": "high number of active AI projects",
        "projects_level(high low)": "high or low number of active AI projects",
        "budget_level(high)": "high AI budget",
        "budget_level(high low)": "high or low AI budget",
        "automation_level(high)": "high automation level",
        "automation_level(high low)": "high or low automation level",
        "company_size(Enterprise)": "enterprise companies",
        "company_size(SME)": "SME companies",
        "company_size(Startup)": "startups",
    }

    parts = [p.strip() for p in cond.split("&")]
    out = []
    for p in parts:
        out.append(replacements.get(p, p))
    return ", ".join(out)

print("=" * 80)
print("HUMAN-READABLE INTERPRETATION OF REPORT RULES")
print("=" * 80)

for i, rule in enumerate(selected_for_report, start=1):
    human_text = humanize_condition(rule["cleaned_antecedent"])
    print(
        f"{i}. Companies with {human_text} show high productivity "
        f"(confidence = {rule['conf']:.1%}, base = {rule['base']})."
    )

print()

# ===============================
# CZECH TEXT FOR PRESENTATION / REPORT
# ===============================
def print_wrapped(text, width=100):
    print("\n".join(textwrap.wrap(text, width=width)))
cz_text = (
    "Výsledky analýzy dále ukazují velmi vysoké hodnoty confidence (často nad 90 %), "
    "což indikuje silnou závislost mezi sledovanými faktory a úrovní produktivity. "
    "Na první pohled by se mohlo zdát, že nalezená pravidla mají vysokou vypovídací hodnotu, "
    "nicméně je nutné interpretovat je s určitou opatrností. "
    "Mnohá pravidla jsou totiž do jisté míry triviální, protože kombinují převážně vysoké "
    "hodnoty vstupních proměnných, což přirozeně vede k vysoké produktivitě. "
    "Tento efekt může být důsledkem charakteru datasetu, který pravděpodobně obsahuje "
    "silné a spíše lineární vazby mezi jednotlivými proměnnými. "
    "Z tohoto důvodu výsledky sice potvrzují očekávané vztahy, avšak nepřinášejí výrazně nové "
    "nebo překvapivé poznatky nad rámec již předpokládaných souvislostí."
)

print("=" * 80)
print("CZECH INTERPRETATION FOR REPORT")
print("=" * 80)
print_wrapped(cz_text, width=100)
print()

