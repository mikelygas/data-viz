import sqlite3
import pandas as pd
import os
import json


def clean_income():
    """Extracts and cleans income data.
    Enters data into SQL database"""

    # Import CSV and convert to dataframes
    income_df = pd.read_csv(
        os.path.join(
            "Resources",
            "NJ_Household_Income.csv"))

    # Drop and rename unnecessary columns and rows
    income_df = income_df[["County", "Household Income"]]
    income_df = income_df.drop(income_df.index[0])
    income_df = income_df.rename(
        columns={
            "County": "COUNTY",
            "Household Income": "INCOME"})

    # Make county column all capitals
    income_df["COUNTY"] = income_df["COUNTY"].str.upper()

    # Verify no missing data
    income_df.isnull().sum()

    # Drop any duplicate rows
    income_df = income_df.drop_duplicates()

    # Review income to verify data is valid
    income_df.INCOME.unique()

    # Verify data is of correct type
    income_df.dtypes

    # Find median income for all of NJ
    income_df["NJ_MED"] = income_df.INCOME.median()

    # Find rank of counties based on income and cast as integer
    income_df["RANK"] = income_df.INCOME.rank(ascending= False)
    income_df["RANK"] = income_df["RANK"].astype("int64")

    # Connect to database and drop/insert "income" table if exists
    conn = sqlite3.connect("nj_db.db")
    income_df.to_sql("income", conn, if_exists="replace")


def clean_geojson_school():
    """Extracts location data from geojson for schools.
    Enters data into SQL database"""

    school_file = open(os.path.join("Resources", "school.geojson"))
    school_json = json.load(school_file)
    school_file.close()

    conn = sqlite3.connect("nj_db.db")
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS school;")
    c.execute("""CREATE TABLE "school" (
        "COUNTY"	TEXT,
        "DIST_CODE"    TEXT,
        "SCHOOLCODE"    TEXT,
        "DS_CODE"       TEXT
        )""")

    rows = []
    for f in school_json["features"]:
        row = []
        row.append(f["properties"]["COUNTY"])
        row.append(f["properties"]["DIST_CODE"])
        row.append(f["properties"]["SCHOOLCODE"])
        row.append(f["properties"]["DIST_CODE"] + "-" +
                   (f["properties"]["SCHOOLCODE"]))
        rows.append(tuple(row))

    c.executemany("INSERT INTO school VALUES (?,?,?,?)", rows)
    conn.commit()
    conn.close()


def clean_school():
    """Extracts and cleans school review data.
    Enters data into SQL database"""

    # Import CSV and convert to dataframes
    test_df = pd.read_csv(os.path.join("Resources", "school_test.csv"))

    # Clean test dataframe

    # Drop and rename columns
    test_df = test_df[["DistrictCode", "SchoolCode",
                       "Test", "Subject", "School_Avg", "State_avg"]]
    test_df = test_df.rename(
        columns={
            "DistrictCode": "DISTRICT_CODE",
            "SchoolCode": "SCHOOL_CODE",
            "SchoolCode": "SCHOOL_CODE",
            "Test": "TEST",
            "School_Avg": "SCH_AVG",
            "State_avg": "STATE_AVG"})

    # Verify no missing data
    test_df.isnull().sum()

    # Drop any duplicate rows
    test_df.drop_duplicates()

    # Add leading zeros to district and school codes
    test_df["DISTRICT_CODE"] = test_df["DISTRICT_CODE"].apply(
        lambda x: "{0:0>4}".format(x))
    test_df["SCHOOL_CODE"] = test_df["SCHOOL_CODE"].apply(
        lambda x: "{0:0>3}".format(x))

    # Create unique key column from district and school codes
    test_df["DS_CODE"] = test_df["DISTRICT_CODE"].map(
        str) + "-" + test_df["SCHOOL_CODE"].map(str)

    # Review ACT scores to verify no missing values and scores within valid
    # range
    ACT_df = test_df[test_df["TEST"].str.contains("ACT")]
    ACT_df.SCH_AVG.unique()
    ACT_df.STATE_AVG.unique()

    # Review SAT scores to verify no missing values and scores within valid
    # range
    SAT_df = test_df[test_df["TEST"].str.contains("SAT")]
    SAT_df.SCH_AVG.unique()
    SAT_df.STATE_AVG.unique()

    # Replace missing values with None and cast as integer
    test_df = test_df.replace(["N", "*"], None)
    test_df["SCH_AVG"] = test_df["SCH_AVG"].astype("int64")

    # Verify values are of the correct type
    test_df.dtypes

    # Filter only SAT scores and separate into columns for Math and English
    test_df = test_df.loc[test_df["TEST"] == "SAT"]
    math_df = test_df.loc[test_df["Subject"] == "Math"]
    english_df = test_df.loc[test_df["Subject"] == "Reading and Writing"]
    english_df = english_df[["DS_CODE", "Subject", "SCH_AVG", "STATE_AVG"]]
    english_df = english_df.rename(
        columns={
            "SCH_AVG": "ENG_SCH_AVG",
            "STATE_AVG": "ENG_STATE_AVG"})
    math_df = math_df.rename(
        columns={
            "SCH_AVG": "MATH_SCH_AVG",
            "STATE_AVG": "MATH_STATE_AVG"})
    math_df = math_df[["Subject", "MATH_SCH_AVG", "MATH_STATE_AVG", "DS_CODE"]]
    test_df = math_df.merge(english_df, on="DS_CODE", how="outer")
    test_df = test_df.drop(labels={"Subject_x", "Subject_y"}, axis=1)

    # Verify no missing data
    test_df.isnull().sum()

    # connect to database and drop/insert "test" table if exists
    conn = sqlite3.connect("nj_db.db")
    test_df.to_sql("test", conn, if_exists="replace")


def csvmap(csvname):
    """Create a score to percentile dictionary used to convert 
    SAT scores to percentages"""
    

    csvpath = os.path.join("Resources", csvname)
    score_to_pctl = {}
    f = open(csvpath)
    headers = None
    
    for line in f:
        if headers == None:
            headers = line
        else:
            parts = line.strip().split(",")
            score = int(parts[0]) 
            pctl = parts[1]
            score_to_pctl[score] = [pctl]
    
    return score_to_pctl


def clean_hospital():
    """Extracts and cleans income data.
    Enters data into SQL database"""

    # Import CSV and convert to dataframes
    hospital_df = pd.read_csv(
        os.path.join(
            "Resources",
            "Hospital_General_Information.csv"))

    # Drop unnecessary columns
    hospital_df = hospital_df[[
        "State", "County Name", "Hospital overall rating"]]

    # Verify no missing data
    hospital_df.isnull().sum()

    # Verify data are of correct type
    hospital_df.dtypes
    hospital_df.infer_objects().dtypes
    hospital_df.dtypes

    # Drop any duplicate rows
    hospital_df.drop_duplicates()

    # Select only hospitals in NJ
    hospital_nj_df = hospital_df[hospital_df["State"] == "NJ"]

    # Drop and rename columns
    hospital_nj_df = hospital_nj_df[["County Name", "Hospital overall rating"]]
    hospital_nj_df = hospital_nj_df.rename(
        columns={
            "County Name": "COUNTY",
            "Hospital overall rating": "RATE"})
    hospital_nj_df = hospital_nj_df[hospital_nj_df["RATE"] != "Not Available"]

    # Connect to database and drop/insert tables if exists
    conn = sqlite3.connect("nj_db.db")
    hospital_nj_df.to_sql("hospitals", conn, if_exists="replace")
