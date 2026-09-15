import pandas as pd

df_filtre = pd.read_csv("data/processed/evenements_filtres.csv")


def test_donnees_filtrees_non_vides():
    assert len(df_filtre) > 0


def test_periode_moins_dun_an():
    cutoff = pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=365)
    dates_fin_utc = pd.to_datetime(df_filtre["lastdate_end"], utc=True)
    assert (dates_fin_utc >= cutoff).all()