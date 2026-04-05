from pathlib import Path
import pandas as pd
import textwrap
from cleverminer import cleverminer

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[2]

INPUT_CSV = PROJECT_ROOT / "out" / "cf_miner" / "prepared_cf_workforce_balance.csv"
OUTPUT_DIR = PROJECT_ROOT / "out" / "cf_miner" / "workforce_balance_top10"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TARGET = "workforce_balance_ord"
TOP_N = 10


def qget(q: dict, *keys):
    for key in keys:
        if key in q:
            return q[key]
    return None


def build_rule_table(clm, target_name: str) -> pd.DataFrame:
    rows = []
    target_categories = clm.get_dataset_category_list(target_name)

    for rule_id in range(1, clm.get_rulecount() + 1):
        q = clm.get_quantifiers(rule_id)
        hist = clm.get_hist(rule_id)

        base = qget(q, "base", "Base", "BASE")
        rel_base = qget(q, "rel_base", "RelBase", "RELBASE")
        s_up = qget(q, "s_up", "S_Up", "S_UP")
        s_down = qget(q, "s_down", "S_Down", "S_DOWN")
        rel_max = qget(q, "rel_max", "RelMax", "RELMAX")
        rel_min = qget(q, "rel_min", "RelMin", "RELMIN")

        contrast_score = None
        if rel_max is not None and rel_min is not None:
            contrast_score = rel_max - rel_min

        rows.append(
            {
                "rule_id": rule_id,
                "rule_text": clm.get_ruletext(rule_id),
                "base": base,
                "rel_base": rel_base,
                "s_up": s_up,
                "s_down": s_down,
                "rel_max": rel_max,
                "rel_min": rel_min,
                "contrast_score": contrast_score,
                "target_categories": " | ".join(map(str, target_categories)),
                "rule_hist": " | ".join(map(str, hist)),
            }
        )

    if not rows:
        return pd.DataFrame()

    df_rules = pd.DataFrame(rows)

    numeric_cols = ["base", "rel_base", "s_up", "s_down", "rel_max", "rel_min", "contrast_score"]
    for col in numeric_cols:
        df_rules[col] = pd.to_numeric(df_rules[col], errors="coerce")

    df_rules = df_rules.sort_values(
        by=["contrast_score", "rel_max", "base"],
        ascending=[False, False, False],
        na_position="last",
    ).reset_index(drop=True)

    return df_rules


def export_top_rules(top_df: pd.DataFrame, output_dir: Path) -> None:
    top_df.to_csv(output_dir / "top10_rules.csv", index=False, encoding="utf-8-sig")


def print_wrapped(text, width=100):
    print("\n".join(textwrap.wrap(text, width=width)))


def print_czech_interpretation() -> None:
    cz_text = (
        "Analýza pomocí CF-Miner ukázala, že i mezi firmami se stejnou, střední úrovní automatizace existují výrazné rozdíly "
        "v dopadu AI na pracovní sílu v závislosti na způsobu jejího využití. "
        "Nejsilnější nalezená pravidla ukazují, že pozitivní dopad na pracovní sílu, tedy vyšší tvorba pracovních míst než jejich úbytek, "
        "je nejvíce spojen s vysokou intenzitou adopce AI. "
        "Obzvláště silné vzory se objevují u firem s vysokou mírou adopce AI v kombinaci s vyšším počtem aktivních AI projektů, "
        "větším počtem používaných AI nástrojů a vyšší úrovní řízení AI rizik. "
        "Výsledky tedy naznačují, že při srovnatelné úrovni automatizace není rozhodující pouze samotná přítomnost AI, "
        "ale především její intenzivní a systematické využívání v organizaci."
    )

    print("=" * 80)
    print("CZECH INTERPRETATION FOR REPORT")
    print("=" * 80)
    print_wrapped(cz_text, width=100)
    print()


def main() -> None:
    print(f"INPUT_CSV = {INPUT_CSV}")
    print(f"OUTPUT_DIR = {OUTPUT_DIR}")

    df = pd.read_csv(INPUT_CSV).astype(str)

    min_base = max(1200, int(len(df) * 0.025))

    print("Input shape:", df.shape)
    print("Chosen Base:", min_base)
    print("No graphs will be generated.")
    print(f"Only top {TOP_N} rules will be printed and saved.")

    clm = cleverminer(
        df=df,
        target=TARGET,
        proc="CFMiner",
        quantifiers={
            "Base": min_base,
            "S_Up": 2,
        },
        cond={
            "attributes": [
                {"name": "regulatory_compliance_ord", "type": "seq", "minlen": 1, "maxlen": 1},
                {"name": "ai_ethics_committee_bin", "type": "subset", "minlen": 1, "maxlen": 1},
                {"name": "ai_risk_management_ord", "type": "seq", "minlen": 1, "maxlen": 1},
                {"name": "ai_adoption_rate_ord", "type": "seq", "minlen": 1, "maxlen": 1},
                {"name": "num_ai_tools_used_ord", "type": "seq", "minlen": 1, "maxlen": 1},
                {"name": "ai_projects_active_ord", "type": "seq", "minlen": 1, "maxlen": 1},
            ],
            "minlen": 1,
            "maxlen": 2,
            "type": "con",
        },
    )

    clm.print_data_definition()
    clm.print_summary()

    if clm.get_rulecount() == 0:
        print("\nNo rules found. Lower Base a bit.")
        return

    rule_df = build_rule_table(clm, TARGET)
    top_df = rule_df.head(TOP_N).copy()

    export_top_rules(top_df, OUTPUT_DIR)

    print(f"\nTOP {TOP_N} RULES:")
    cols_to_show = [
        "rule_id",
        "rule_text",
        "base",
        "rel_base",
        "rel_min",
        "rel_max",
        "contrast_score",
        "rule_hist",
    ]
    print(top_df[cols_to_show].to_string(index=False))

    print(f"\nSaved top {TOP_N} rules to: {OUTPUT_DIR / 'top10_rules.csv'}\n")

    print_czech_interpretation()


if __name__ == "__main__":
    main()