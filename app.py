# Import dependencies
import json
import sqlite3
import os
import statistics
import math
from flask import (
    Flask,
    render_template,
    jsonify)
from clean import (
    clean_geojson_school,
    clean_school,
    csvmap,
    clean_income,
    clean_hospital)


# Set up Flask
app = Flask(__name__)

# Create database
conn = sqlite3.connect("nj_db.db")

# Add geojson data to database
school_file = open(os.path.join("Resources", "school.geojson"))
school_json = json.load(school_file)

# Set variable for county geojson to be passed in route
county_file = open(os.path.join("Resources", "counties.geojson"))
county_json = json.load(county_file)

# Clean data and import into database
clean_geojson_school()
clean_school()
clean_hospital()
clean_income()


#Create routes 

@app.route("/")
def index():
    """Render the homepage."""
    

    return render_template("index.html")


@app.route("/counties/location")
def counties_locations():
    """Returns geojson of countiesf for NJ"""
    
    return jsonify(county_json)


@app.route("/counties")
def counties():
    """Returns list of counties for NJ"""


    conn = sqlite3.connect("nj_db.db")
    c = conn.cursor()
    data = c.execute("SELECT DISTINCT COUNTY FROM hospitals").fetchall()
    
    return jsonify(data)


@app.route("/income/state")
def income():
    """Returns jsonified list of income for all counties in NJ"""


    conn = sqlite3.connect("nj_db.db")
    c = conn.cursor()
    data = c.execute("""SELECT COUNTY, INCOME, NJ_MED, RANK
        FROM income""").fetchall()
    conn.commit()
    conn.close()

    income_dict=[]
    for d in data:
        dict={"county": d[0] ,"income": d[1], "nj_med": d[2], "rank": d[3]}
        income_dict.append(dict)
    
    return jsonify(income_dict)


@app.route("/income/counties/<COUNTY>")
def income_county(COUNTY):
    """Returns jsonified list of income for all counties in NJ"""

    conn = sqlite3.connect("nj_db.db")
    c = conn.cursor()
    query = """SELECT COUNTY, INCOME, NJ_MED, RANK
       FROM INCOME
       WHERE COUNTY = ?"""
    data = c.execute(query,[COUNTY]).fetchall()
    conn.commit()
    conn.close()

    income_dict=[]
    for d in data:
        dict={"county": d[0] ,"income": d[1], "nj_med": d[2], "rank": d[3]}
        income_dict.append(dict)
    
    return jsonify(income_dict)


@app.route("/school/counties/<COUNTY>")
def school_county(COUNTY):
    """Returns jsonified list of average SAT scores for county and state"""


    conn = sqlite3.connect("nj_db.db")
    c = conn.cursor()

    query="""SELECT SCHOOL.COUNTY county,
        ROUND(AVG(test.MATH_SCH_AVG), 2) math_avg, ROUND(AVG(test.ENG_SCH_AVG), 2) eng_avg,
        ROUND((AVG(test.MATH_SCH_AVG)+AVG(test.ENG_SCH_AVG)),2) total_avg,
        ROUND(AVG(test.MATH_STATE_AVG), 2) math_state_avg, ROUND(AVG(TEST.ENG_STATE_AVG), 2) eng_state_avg
        FROM school
        JOIN test ON TEST.DS_CODE=SCHOOL.DS_CODE
        WHERE school.county = ?
        GROUP BY school.county"""
    
    data = c.execute(query,[COUNTY]).fetchall()
    school_list=[]
    
    #Pass parameters to open csv file and return dictionary
    csvtest = csvmap("SATmapMATH.csv")
    csvRW = csvmap("SATmapRW.csv")

    #Loop thru rows and calculate county math and eng avg and percentile
    for row in data:
        math_avg = 10*math.ceil(row[1]/10)
        eng_avg = 10*math.ceil(row[2]/10)
        math_pctl = csvtest[math_avg][0]
        eng_pctl = csvRW[eng_avg][0]
        school={"county":row[0],"math_avg":row[1],"eng_avg":row[2],"total_avg":row[3],"math_state_avg":row[4],
        "eng_state_avg":row[5],"math_pctl":math_pctl,"eng_pctl":eng_pctl}
        school_list.append(school)
    conn.commit()
    conn.close()
    return jsonify(school_list)

  
@app.route("/hospital/counties/<COUNTY>")
def hospital_county(COUNTY):
    """Returns jsonified list of rating information for hospitals
    in specified county"""


    conn = sqlite3.connect("nj_db.db")
    c = conn.cursor()
    
    query2="""SELECT H.COUNTY, H.RATE
        FROM hospitals H
        WHERE COUNTY = ?"""
    
    data = c.execute(query2,[COUNTY]).fetchall()
    
    hospitals_list=[]
    for d in data:
        row={"county":d[0], "rate":d[1]}
        hospitals_list.append(row)
    
    rate = [int(x[1]) for x in data]
    median_rate = statistics.median(rate)
    
    hospitals_stats = {"median": median_rate}
    hospitals_dict = {"list": hospitals_list, "stats": hospitals_stats}
    
    conn.commit()
    conn.close()
    
    return jsonify(hospitals_dict)

   
@app.route("/school/state")
def school_state():
    """Returns jsonified list of average SAT scores for state """

    conn = sqlite3.connect("nj_db.db")
    c = conn.cursor()
    
    query_s="""SELECT SCHOOL.COUNTY county,
     (ROUND(AVG(TEST.MATH_SCH_AVG), 2)+ ROUND(AVG(TEST.ENG_SCH_AVG), 2))AS ENG_MATH_SUM
       FROM SCHOOL
       JOIN TEST ON TEST.DS_CODE=SCHOOL.DS_CODE
       GROUP BY SCHOOL.COUNTY"""

    data=c.execute(query_s).fetchall()
    test_dict=[]
    for row in data:
        dict={"county": row[0], "sat_avg":row[1]}
        test_dict.append(dict)
    
    conn.commit()
    conn.close()
    
    return jsonify(test_dict)


@app.route("/hospital/state")
def hospital_state():
    """Returned jsonified list of hospitals and ratings
    for state"""

    conn = sqlite3.connect("nj_db.db")
    c = conn.cursor()
    
   
    query="""SELECT COUNTY, ROUND(AVG(RATE), 2) avg_rate
        FROM hospitals
        GROUP BY COUNTY"""
    
    data=c.execute(query).fetchall()
    
    hosp_county_dict=[]
    for row in data:
        dict={"county":row[0],"avg_rate":row[1]}
        hosp_county_dict.append(dict)
    
    conn.commit()
    conn.close()
    
    return jsonify(hosp_county_dict)


if __name__ == "__main__":
    app.run(debug=False, port=8000, host="localhost", threaded=True)