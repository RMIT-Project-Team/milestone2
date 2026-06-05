from flask import Flask, render_template, request, jsonify, Response
import sqlite3
import csv
import io
import os

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(__file__), 'Road_Accidents.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_site_tables():
    """Create + populate the Level-1 content tables (mission, how-to, personas,
    team) if they don't already exist, so the app runs on a fresh DB clone.
    These store the Sub-Task B Level 1 content that must come from the database."""
    conn = get_db()
    c = conn.cursor()
    c.executescript('''
        CREATE TABLE IF NOT EXISTS Site_Mission (
            id INTEGER PRIMARY KEY, mission_text TEXT, social_challenge TEXT);
        CREATE TABLE IF NOT EXISTS Site_HowTo (
            step_order INTEGER PRIMARY KEY, step_title TEXT, step_desc TEXT);
        CREATE TABLE IF NOT EXISTS Site_Persona (
            persona_id INTEGER PRIMARY KEY, name TEXT, quote TEXT, age INTEGER,
            occupation TEXT, organisation TEXT, location TEXT, subtask TEXT, description TEXT);
        CREATE TABLE IF NOT EXISTS Team_Member (
            student_id TEXT PRIMARY KEY, name TEXT, subtask TEXT);
    ''')
    c.execute('SELECT COUNT(*) AS n FROM Site_Mission')
    if c.fetchone()['n'] == 0:
        c.execute("INSERT INTO Site_Mission VALUES (1, ?, ?)", (
            "VicRoadInsight helps road safety analysts and public health researchers explore "
            "Victorian crash data from 2013 to 2025. We make it easy to filter, summarise and "
            "discover risk patterns across environmental conditions and people — without manual "
            "CSV exports or data wrangling.",
            "Victoria recorded hundreds of road deaths last year, above the long-term average. "
            "Despite a Safe System strategy targeting zero fatalities, road trauma remains a "
            "serious public health challenge. The data exists but is scattered and hard to use. "
            "VicRoadInsight bridges that gap."))
        c.executemany('INSERT INTO Site_HowTo VALUES (?,?,?)', [
            (1, 'Pick a pathway', 'Choose Conditions Analysis for road/weather/light data, or People & Injuries for demographic and outcome data.'),
            (2, 'Apply filters', 'Use the sidebar to filter by age, sex, road user type, ejection status or hospitalisation.'),
            (3, 'View results', 'See a summarised table and chart showing the data matching your filters.'),
            (4, 'Deep-dive', 'Visit the Deep-Dive page to discover above-average risk profiles surfaced automatically by the system.')])
        c.executemany('INSERT INTO Site_Persona VALUES (?,?,?,?,?,?,?,?,?)', [
            (1, 'Marcus Chen', 'I need to know which conditions are actually dangerous, not just the ones that happen most often.',
             34, 'Road Safety Analyst', 'Department of Transport and Planning Victoria', 'Docklands, Melbourne VIC', 'Sub-Task A',
             'Marcus analyses crash data and prepares briefings for government. He needs to filter crashes by road surface, weather and light conditions to build evidence-based infrastructure proposals.'),
            (2, 'Dr. Priya Nair', 'The data exists — we just cannot access it in a way that answers the questions that actually matter for public health.',
             41, 'Public Health Researcher', 'Monash University Accident Research Centre (MUARC)', 'Clayton, Melbourne VIC', 'Sub-Task B',
             'Dr. Nair leads injury prevention research at MUARC. She needs to combine demographic data with injury outcomes to identify at-risk populations and design targeted prevention campaigns.')])
        c.executemany('INSERT INTO Team_Member VALUES (?,?,?)', [
            ('S4212298', 'Manpreet Singh', 'Sub-Task A'),
            ('S4153861', 'Saeed Alawadhi', 'Sub-Task B')])
        conn.commit()
    conn.close()

# ─── LANDING PAGE (Sub-Task A Level 1) ───────────────────────────────────────
@app.route('/')
def index():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT COUNT(*) as val FROM Accident')
    total_crashes = c.fetchone()['val']
    c.execute('SELECT SUM(NO_PERSONS_KILLED) as val FROM Accident')
    total_killed = c.fetchone()['val']
    c.execute('SELECT SUM(NO_PERSONS_INJ_SERIOUS) as val FROM Accident')
    serious_inj = c.fetchone()['val']
    c.execute("SELECT MIN(substr(ACCIDENT_DATE,-4)) as mn, MAX(substr(ACCIDENT_DATE,-4)) as mx FROM Accident")
    yr = c.fetchone()
    year_range = f"{yr['mn']}–{yr['mx']}"
    conn.close()
    facts = [
        {'label': 'Total Crashes', 'value': f"{total_crashes:,}", 'icon': '🚗', 'desc': 'Reported road crashes across Victoria'},
        {'label': 'Fatalities', 'value': f"{total_killed:,}", 'icon': '📋', 'desc': 'Lives lost on Victorian roads'},
        {'label': 'Serious Injuries', 'value': f"{serious_inj:,}", 'icon': '🏥', 'desc': 'Persons seriously injured'},
        {'label': 'Years of Data', 'value': year_range, 'icon': '📅', 'desc': 'Historical dataset coverage'},
    ]
    return render_template('index.html', facts=facts)

# ─── MISSION STATEMENT (Sub-Task B Level 1) ──────────────────────────────────
@app.route('/about')
def about():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM Site_Mission WHERE id = 1')
    mission = c.fetchone()
    c.execute('SELECT * FROM Site_HowTo ORDER BY step_order')
    steps = c.fetchall()
    c.execute('SELECT * FROM Site_Persona ORDER BY persona_id')
    personas = c.fetchall()
    c.execute('SELECT * FROM Team_Member ORDER BY student_id')
    team = c.fetchall()
    conn.close()
    return render_template('about.html', mission=mission, steps=steps, personas=personas, team=team)

# ─── CONDITIONS (Sub-Task A Level 2) ─────────────────────────────────────────
@app.route('/conditions')
def conditions():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM Road_Surface_Cond WHERE SURFACE_COND != 9 ORDER BY SURFACE_COND_DESC')
    surfaces = c.fetchall()
    c.execute('SELECT * FROM Amospheric_Cond WHERE ATMOSPH_COND != 9 ORDER BY ATMOSPH_COND_DESC')
    atmospherics = c.fetchall()
    c.execute('SELECT * FROM Light_Condition WHERE COND_ID != 9 ORDER BY COND_NAME')
    lights = c.fetchall()
    conn.close()
    return render_template('conditions.html', surfaces=surfaces, atmospherics=atmospherics, lights=lights)

@app.route('/api/conditions')
def api_conditions():
    surface = request.args.get('surface', '')
    weather = request.args.get('weather', '')
    light = request.args.get('light', '')
    year_from = request.args.get('year_from', '2013')
    year_to = request.args.get('year_to', '2025')
    sort_col = request.args.get('sort', 'total_crashes')
    sort_dir = request.args.get('dir', 'desc')

    allowed_sorts = {'total_crashes', 'fatalities', 'serious_injuries', 'fatal_pct'}
    if sort_col not in allowed_sorts:
        sort_col = 'total_crashes'
    if sort_dir not in ('asc', 'desc'):
        sort_dir = 'desc'

    params = []
    where_clauses = [
        "acs.ATMOSPH_COND != 9",
        "scs.SURFACE_COND != 9",
        "a.LIGHT_CONDITION != 9",
        "CAST(substr(a.ACCIDENT_DATE, -4) AS INTEGER) BETWEEN ? AND ?"
    ]
    params += [int(year_from), int(year_to)]

    if surface:
        where_clauses.append("scs.SURFACE_COND = ?")
        params.append(int(surface))
    if weather:
        where_clauses.append("acs.ATMOSPH_COND = ?")
        params.append(int(weather))
    if light:
        where_clauses.append("a.LIGHT_CONDITION = ?")
        params.append(int(light))

    where_sql = " AND ".join(where_clauses)

    query = f"""
        SELECT
            rsc.SURFACE_COND_DESC as surface,
            ac.ATMOSPH_COND_DESC as atmosphere,
            lc.COND_NAME as light,
            COUNT(DISTINCT a.ACCIDENT_NO) as total_crashes,
            SUM(a.NO_PERSONS_KILLED) as fatalities,
            SUM(a.NO_PERSONS_INJ_SERIOUS) as serious_injuries,
            ROUND(100.0 * SUM(a.NO_PERSONS_KILLED) / NULLIF(COUNT(DISTINCT a.ACCIDENT_NO), 0), 2) as fatal_pct
        FROM Accident a
        JOIN Atmospheric_Cond_Seq acs ON a.ACCIDENT_NO = acs.ACCIDENT_NO AND acs.ATMOSPH_COND_SEQ = 1
        JOIN Surface_Cond_Seq scs ON a.ACCIDENT_NO = scs.ACCIDENT_NO AND scs.SURFACE_COND_SEQ = 1
        JOIN Amospheric_Cond ac ON acs.ATMOSPH_COND = ac.ATMOSPH_COND
        JOIN Road_Surface_Cond rsc ON scs.SURFACE_COND = rsc.SURFACE_COND
        JOIN Light_Condition lc ON a.LIGHT_CONDITION = lc.COND_ID
        WHERE {where_sql}
        GROUP BY acs.ATMOSPH_COND, scs.SURFACE_COND, a.LIGHT_CONDITION
        ORDER BY {sort_col} {sort_dir}
        LIMIT 100
    """
    conn = get_db()
    c = conn.cursor()
    c.execute(query, params)
    rows = [dict(r) for r in c.fetchall()]

    # Chart data: totals by atmosphere
    c.execute("""
        SELECT ac.ATMOSPH_COND_DESC as label, COUNT(DISTINCT a.ACCIDENT_NO) as value
        FROM Accident a
        JOIN Atmospheric_Cond_Seq acs ON a.ACCIDENT_NO = acs.ACCIDENT_NO AND acs.ATMOSPH_COND_SEQ = 1
        JOIN Amospheric_Cond ac ON acs.ATMOSPH_COND = ac.ATMOSPH_COND
        WHERE acs.ATMOSPH_COND != 9
        GROUP BY acs.ATMOSPH_COND
        ORDER BY value DESC
    """)
    chart = [dict(r) for r in c.fetchall()]
    conn.close()
    return jsonify({'rows': rows, 'chart': chart, 'count': len(rows)})

# ─── PEOPLE & INJURIES (Sub-Task B Level 2) ──────────────────────────────────
@app.route('/people')
def people():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT DISTINCT AGE_GROUP FROM Person WHERE AGE_GROUP NOT IN ("Unknown","","5-Dec") ORDER BY AGE_GROUP')
    age_groups_raw = [r['AGE_GROUP'] for r in c.fetchall()]
    # Sort sensibly
    age_order = ['0-4','13-15','16-17','18-21','22-25','26-29','30-39','40-49','50-59','60-64','65-69','70+']
    age_groups = [a for a in age_order if a in age_groups_raw]

    c.execute('SELECT * FROM Road_User WHERE ROAD_USER_TYPE NOT IN (9) ORDER BY ROAD_USER_TYPE_DESC')
    road_users = c.fetchall()
    c.execute('SELECT * FROM Ejection ORDER BY EJECTED_CODE')
    ejections = c.fetchall()
    conn.close()
    return render_template('people.html', age_groups=age_groups, road_users=road_users, ejections=ejections)

@app.route('/api/people')
def api_people():
    age = request.args.get('age', '')
    sex = request.args.get('sex', '')
    road_user = request.args.get('road_user', '')
    ejected = request.args.get('ejected', '')
    hospital = request.args.get('hospital', '')
    sort_col = request.args.get('sort', 'fatalities')
    sort_dir = request.args.get('dir', 'desc')
    export = request.args.get('export', '')

    allowed_sorts = {'persons', 'fatalities', 'serious_injuries', 'hosp_rate', 'eject_rate'}
    if sort_col not in allowed_sorts:
        sort_col = 'fatalities'
    if sort_dir not in ('asc', 'desc'):
        sort_dir = 'desc'

    where_clauses = ["p.SEX IN ('M','F')", "p.AGE_GROUP NOT IN ('Unknown','','5-Dec')"]
    params = []

    if age:
        where_clauses.append("p.AGE_GROUP = ?")
        params.append(age)
    if sex:
        where_clauses.append("p.SEX = ?")
        params.append(sex)
    if road_user:
        where_clauses.append("p.ROAD_USER_TYPE = ?")
        params.append(int(road_user))
    if ejected:
        where_clauses.append("p.EJECTED_CODE = ?")
        params.append(int(ejected))
    if hospital:
        where_clauses.append("p.TAKEN_HOSPITAL = ?")
        params.append(hospital)

    where_sql = " AND ".join(where_clauses)

    query = f"""
        SELECT
            CASE WHEN p.SEX = 'M' THEN 'Male' ELSE 'Female' END as sex_label,
            p.AGE_GROUP,
            ru.ROAD_USER_TYPE_DESC as road_user,
            COUNT(*) as persons,
            SUM(CASE WHEN p.INJ_LEVEL = 1 THEN 1 ELSE 0 END) as fatalities,
            SUM(CASE WHEN p.INJ_LEVEL = 2 THEN 1 ELSE 0 END) as serious_injuries,
            ROUND(100.0 * SUM(CASE WHEN p.TAKEN_HOSPITAL = 'Y' THEN 1 ELSE 0 END) / COUNT(*), 1) as hosp_rate,
            ROUND(100.0 * SUM(CASE WHEN p.EJECTED_CODE IN (1,2,3) THEN 1 ELSE 0 END) / COUNT(*), 1) as eject_rate
        FROM Person p
        JOIN Road_User ru ON p.ROAD_USER_TYPE = ru.ROAD_USER_TYPE
        WHERE {where_sql}
        GROUP BY p.SEX, p.AGE_GROUP, p.ROAD_USER_TYPE
        ORDER BY {sort_col} {sort_dir}
        LIMIT 200
    """
    conn = get_db()
    c = conn.cursor()
    c.execute(query, params)
    rows = [dict(r) for r in c.fetchall()]

    # Injury severity distribution for donut
    inj_query = f"""
        SELECT i.INJ_LEVEL_DESC as label, COUNT(*) as value
        FROM Person p
        JOIN Injury i ON p.INJ_LEVEL = i.INJ_LEVEL
        JOIN Road_User ru ON p.ROAD_USER_TYPE = ru.ROAD_USER_TYPE
        WHERE {where_sql}
        GROUP BY p.INJ_LEVEL
        ORDER BY p.INJ_LEVEL
    """
    c.execute(inj_query, params)
    donut = [dict(r) for r in c.fetchall()]
    conn.close()

    if export == 'csv':
        si = io.StringIO()
        writer = csv.DictWriter(si, fieldnames=['sex_label','AGE_GROUP','road_user','persons','fatalities','serious_injuries','hosp_rate','eject_rate'])
        writer.writeheader()
        writer.writerows(rows)
        output = si.getvalue()
        return Response(output, mimetype='text/csv',
                        headers={'Content-Disposition': 'attachment;filename=people_injuries.csv'})

    return jsonify({'rows': rows, 'donut': donut, 'count': len(rows)})

# ─── DEEP DIVE (Sub-Task B Level 3) ──────────────────────────────────────────
@app.route('/deepdive')
def deepdive():
    return render_template('deepdive.html')

@app.route('/api/deepdive')
def api_deepdive():
    dimension = request.args.get('dimension', 'age_user')  # age_user | age_only | user_only

    if dimension == 'age_only':
        group_cols = "p.AGE_GROUP"
        label_expr = "p.AGE_GROUP as profile"
    elif dimension == 'user_only':
        group_cols = "p.ROAD_USER_TYPE"
        label_expr = "ru.ROAD_USER_TYPE_DESC as profile"
    else:  # age_user (default)
        group_cols = "p.SEX, p.AGE_GROUP, p.ROAD_USER_TYPE"
        label_expr = "CASE WHEN p.SEX='M' THEN 'Male' ELSE 'Female' END || ' ' || p.AGE_GROUP || ' ' || ru.ROAD_USER_TYPE_DESC as profile"

    query = f"""
        WITH group_stats AS (
            SELECT
                {label_expr},
                COUNT(*) as persons,
                SUM(CASE WHEN p.INJ_LEVEL = 1 THEN 1 ELSE 0 END) as fatalities,
                SUM(CASE WHEN p.INJ_LEVEL = 2 THEN 1 ELSE 0 END) as serious_injuries,
                ROUND(100.0 * SUM(CASE WHEN p.INJ_LEVEL IN (1,2) THEN 1 ELSE 0 END) / COUNT(*), 2) as serious_rate,
                ROUND(100.0 * SUM(CASE WHEN p.INJ_LEVEL = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) as fatal_rate,
                ROUND(100.0 * SUM(CASE WHEN p.EJECTED_CODE IN (1,2,3) THEN 1 ELSE 0 END) / COUNT(*), 2) as eject_rate
            FROM Person p
            JOIN Road_User ru ON p.ROAD_USER_TYPE = ru.ROAD_USER_TYPE
            WHERE p.SEX IN ('M','F') AND p.AGE_GROUP NOT IN ('Unknown','','5-Dec')
            GROUP BY {group_cols}
            HAVING COUNT(*) >= 50
        ),
        avg_stats AS (
            SELECT ROUND(AVG(serious_rate), 2) as avg_rate FROM group_stats
        )
        SELECT gs.*, ar.avg_rate,
               RANK() OVER (ORDER BY gs.serious_rate DESC) as rank
        FROM group_stats gs, avg_stats ar
        WHERE gs.serious_rate > ar.avg_rate
        ORDER BY gs.serious_rate DESC
    """

    conn = get_db()
    c = conn.cursor()
    c.execute(query)
    rows = [dict(r) for r in c.fetchall()]

    # Heatmap data: age x road_user serious rate
    c.execute("""
        SELECT p.AGE_GROUP, ru.ROAD_USER_TYPE_DESC as road_user,
               ROUND(100.0 * SUM(CASE WHEN p.INJ_LEVEL IN (1,2) THEN 1 ELSE 0 END) / COUNT(*), 1) as rate
        FROM Person p
        JOIN Road_User ru ON p.ROAD_USER_TYPE = ru.ROAD_USER_TYPE
        WHERE p.SEX IN ('M','F') AND p.AGE_GROUP NOT IN ('Unknown','','5-Dec')
          AND ru.ROAD_USER_TYPE IN (1,2,3,4,6,16)
        GROUP BY p.AGE_GROUP, p.ROAD_USER_TYPE
        HAVING COUNT(*) >= 30
    """)
    heatmap = [dict(r) for r in c.fetchall()]
    conn.close()

    avg_rate = rows[0]['avg_rate'] if rows else 0
    return jsonify({'rows': rows, 'heatmap': heatmap, 'avg_rate': avg_rate, 'count': len(rows)})

if __name__ == '__main__':
    init_site_tables()
    app.run(debug=True, port=5000)
