import pandas as pd
import datetime as dt

df = pd.read_json("data/data.json")

def test_donnees_non_vides():
    assert len(df) > 0

def test_region_bretagne():
    assert (df["location_region"] == "Bretagne").all()


def test_uid_uniques():
    assert df["uid"].is_unique