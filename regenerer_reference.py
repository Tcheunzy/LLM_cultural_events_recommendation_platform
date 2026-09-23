import json
from pathlib import Path

from src.indexation import charger_documents
from src.preparation import charger_df_evenements_final

PROJECT_ROOT = Path(__file__).resolve().parent
CHEMIN_DATA = PROJECT_ROOT / "data" / "data.json"

# evenements_filtres.csv (utilisé par tests/test_filtrage.py)
df_evenements_final = charger_df_evenements_final(str(CHEMIN_DATA))
chemin_csv = PROJECT_ROOT / "data" / "processed" / "evenements_filtres.csv"
df_evenements_final.to_csv(chemin_csv, index=False)
print(f"{len(df_evenements_final)} événements écrits dans {chemin_csv}")

# uids_attendus.json (utilisé par tests/test_indexation.py)
documents = charger_documents(str(CHEMIN_DATA))
uids_attendus = [doc.metadata["uids"] for doc in documents]
chemin_json = PROJECT_ROOT / "data" / "index" / "uids_attendus.json"
with open(chemin_json, "w", encoding="utf-8") as f:
    json.dump(uids_attendus, f, ensure_ascii=False)
print(f"{len(uids_attendus)} événements écrits dans {chemin_json}")