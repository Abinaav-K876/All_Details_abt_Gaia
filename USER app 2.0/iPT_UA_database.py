import datetime
import mimetypes
import smtplib
import threading
from email.message import EmailMessage
import psycopg2
import sqlite3
from themes import pink, lavender_og, blue, green, orange
import json, os
import random
from datetime import datetime, timedelta

'''
local databases

-user login details
-drones
-air nodes
-water nodes
-settings


conn = sqlite3.connect("gaia_local.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS user_login_details (
    is_logged_in TEXT,
    username TEXT,
    user_mail TEXT,
    profile_pic TEXT,
    is_profile_pic TEXT)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS drones (
    name_drone TEXT)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS air_nodes (
    name_air_node TEXT)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS water_nodes (
    name_water_node TEXT)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS genesis_nodes (
    name_hepa_node TEXT)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS hepa_nodes (
    name_hepa_node TEXT)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS no_of_drw (
    no_of_drones TEXT,
    no_of_air_nodes TEXT,
    no_of_water_nodes TEXT)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS settings (
    list_user_settings TEXT,
    list_default_settings TEXT,
    list_of_current_used_images TEXT)
""")

conn.commit()
conn.close()
'''

def get_all_names_air_nodes_offline():
    conn = sqlite3.connect("gaia_local.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM air_nodes")
    result = cur.fetchall()
    conn.close()
    return result

def add_air_node_offline(name):
    conn = sqlite3.connect("gaia_local.db")
    cur = conn.cursor()
    cur.execute(f"""INSERT INTO air_nodes VALUES('{name}');""")
    conn.commit()
    conn.close()

def remove_air_node_offline(name):
    conn = sqlite3.connect("gaia_local.db")
    cur = conn.cursor()
    cur.execute(f"""DELETE FROM air_nodes WHERE name_air_node='{name}';""")
    conn.commit()
    conn.close()

def get_all_names_water_nodes_offline():
    conn = sqlite3.connect("gaia_local.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM water_nodes")
    result = cur.fetchall()
    conn.close()
    return result

def add_water_node_offline(name):
    conn = sqlite3.connect("gaia_local.db")
    cur = conn.cursor()
    cur.execute(f"""INSERT INTO water_nodes VALUES('{name}');""")
    conn.commit()
    conn.close()

def remove_water_node_offline(name):
    conn = sqlite3.connect("gaia_local.db")
    cur = conn.cursor()
    cur.execute(f"""DELETE FROM water_nodes WHERE name_water_node='{name}';""")
    conn.commit()
    conn.close()

def get_all_names_hepa_nodes_offline():
    conn = sqlite3.connect("gaia_local.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM hepa_nodes")
    result = cur.fetchall()
    conn.close()
    return result

def add_hepa_node_offline(name):
    conn = sqlite3.connect("gaia_local.db")
    cur = conn.cursor()
    cur.execute(f"""INSERT INTO hepa_nodes VALUES('{name}');""")
    conn.commit()
    conn.close()

def remove_hepa_node_offline(name):
    conn = sqlite3.connect("gaia_local.db")
    cur = conn.cursor()
    cur.execute(f"""DELETE FROM hepa_nodes WHERE name_hepa_node='{name}';""")
    conn.commit()
    conn.close()

def get_all_names_genesis_nodes_offline():
    conn = sqlite3.connect('gaia_local.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM genesis_nodes")
    result = cur.fetchall()
    conn.close()
    return result

def add_genesis_node_offline(name):
    conn = sqlite3.connect('gaia_local.db')
    cur = conn.cursor()
    cur.execute(f"INSERT INTO genesis_nodes VALUES('{name}')")
    conn.commit()
    conn.close()

def remove_genesis_node_offline(name):
    conn = sqlite3.connect('gaia_local.db')
    cur = conn.cursor()
    cur.execute(f"DELETE FROM genesis_nodes WHERE name_genesis_node='{name}'")
    conn.commit()
    conn.close()

def create_databases_online():
    connection = psycopg2.connect(host=host, database=database, user=user, password=password, port=port)
    conn = connection.cursor()

    conn.execute("""CREATE TABLE IF NOT EXISTS users(
                    username TEXT,
                    email TEXT,
                    password TEXT,
                    gender TEXT,
                    dob TEXT,
                    profile_pic TEXT,
                    if_profile TEXT,
                    state TEXT,
                    city TEXT)""")

    conn.execute("""CREATE TABLE IF NOT EXISTS drones(
                    drone_name TEXT,
                    bat_status TEXT,
                    activity_status TEXT,
                    current_mode TEXT,
                    camera_feed_link TEXT,
                    current_direction TEXT,
                    air_node_name TEXT,
                    avaliable_to_connect TEXT)""")

    # ⚠️ UPDATED: air_node now stores MQ2, MQ4, MQ6 as well
    conn.execute("""CREATE TABLE IF NOT EXISTS air_node(
                    air_node_name TEXT,
                    password TEXT,
                    mq135 TEXT,
                    mq7 TEXT,
                    mq2 TEXT,
                    mq4 TEXT,
                    mq6 TEXT,
                    dht22_hum TEXT,
                    dht22_temp TEXT,
                    activity_status TEXT,
                    bat_status TEXT,
                    avaliable_to_connect TEXT)""")

    conn.execute("""CREATE TABLE IF NOT EXISTS water_node(
                    water_node_name TEXT,
                    password TEXT,
                    tds TEXT,
                    dsi8 TEXT,
                    activity_status TEXT,
                    bat_status TEXT,
                    avaliable_to_connect TEXT)""")

    conn.execute("""CREATE TABLE IF NOT EXISTS hepa_node(
                    hepa_node_name TEXT,
                    password TEXT,
                    aqi TEXT,
                    ps TEXT,
                    activity_status TEXT,
                    bat_status TEXT,
                    avaliable_to_connect TEXT)""")

    # Air Node History (All sensors)
    conn.execute("""CREATE TABLE IF NOT EXISTS air_node_history (
                    id SERIAL PRIMARY KEY,
                    node_name TEXT,
                    mq135 INTEGER, mq7 INTEGER, mq2 INTEGER, mq4 INTEGER, mq6 INTEGER,
                    temp DECIMAL(5,2), humidity DECIMAL(5,2),
                    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )""")

    # Water Node History
    conn.execute("""CREATE TABLE IF NOT EXISTS water_node_history (
                    id SERIAL PRIMARY KEY,
                    node_name TEXT,
                    tds INTEGER,
                    dsi8 DECIMAL(5,2),
                    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )""")

    # Hepa Node History
    conn.execute("""CREATE TABLE IF NOT EXISTS hepa_node_history (
                    id SERIAL PRIMARY KEY,
                    node_name TEXT,
                    aqi INTEGER, 
                    ps TEXT,
                    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )""")

    # Add Genesis Node table
    conn.execute("""
            CREATE TABLE IF NOT EXISTS genesis_node (
                genesis_node_name TEXT,
                password TEXT,
                aqi TEXT,
                aqi_output TEXT,
                lux TEXT,
                ps TEXT,
                activity_status TEXT,
                bat_status TEXT,
                avaliable_to_connect TEXT
            )
        """)

    # Add Genesis Node History table
    conn.execute("""
            CREATE TABLE IF NOT EXISTS genesis_node_history (
                id SERIAL PRIMARY KEY,
                node_name TEXT,
                aqi_input INTEGER,
                aqi_output INTEGER,
                lux INTEGER,
                ps TEXT,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

    # Alerts Table
    conn.execute("""CREATE TABLE IF NOT EXISTS system_alerts (
                    id SERIAL PRIMARY KEY,
                    user_email TEXT,
                    type TEXT,
                    message TEXT,
                    is_read BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )""")

    conn.execute("""CREATE TABLE IF NOT EXISTS rank_holder_cities(
                    state TEXT,
                    city TEXT,
                    mq135 TEXT,
                    mq7 TEXT,
                    dht_hum TEXT,
                    dht_temp TEXT,
                    ur_place_state TEXT,
                    ur_place_country TEXT)""")

    conn.execute("""CREATE TABLE IF NOT EXISTS indi_rank(
                    place TEXT,
                    email TEXT,
                    aqi TEXT)""")

    conn.execute("""CREATE TABLE IF NOT EXISTS city_data(
                    state TEXT,
                    city TEXT,
                    mq135 TEXT,
                    mq7 TEXT,
                    dht_hum TEXT,
                    dht_temp TEXT)""")

    connection.commit()
    conn.close()
    connection.close()

def get_all_air_nodes_data_bulk():
    """Fetch essential data for ALL air nodes in one query to improve performance."""
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        # Fetch name, mq135 (AQI proxy), activity_status
        cur.execute("SELECT air_node_name, mq135, activity_status FROM air_node")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows # [(name, mq135, status), ...]
    except Exception as e:
        print(f"Bulk Air Fetch Error: {e}")
        return []

def get_all_water_nodes_data_bulk():
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        # Fetch name, tds, activity_status
        cur.execute("SELECT water_node_name, tds, activity_status FROM water_node")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows
    except Exception as e:
        print(f"Bulk Water Fetch Error: {e}")
        return []

def get_all_hepa_nodes_data_bulk():
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        # Fetch name, aqi, activity_status
        cur.execute("SELECT hepa_node_name, aqi, activity_status FROM hepa_node")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows
    except Exception as e:
        print(f"Bulk HEPA Fetch Error: {e}")
        return []

def get_db_conn():
    conn = psycopg2.connect(host=host, database=database, user=user, password=password, port=port)
    return conn

def log_air_data(node_name, mq135, mq7, mq2, mq4, mq6, temp, hum):
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        sql = """INSERT INTO air_node_history 
                 (node_name, mq135, mq7, mq2, mq4, mq6, temp, humidity, recorded_at)
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())"""
        cur.execute(sql, (node_name, mq135, mq7, mq2, mq4, mq6, temp, hum))
        conn.commit()
        conn.close()
        print(f"✅ Logged Air Data for {node_name}")
    except Exception as e: print(f"❌ Air Log Error: {e}")

def log_water_data(node_name, tds, dsi8):
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        sql = """INSERT INTO water_node_history (node_name, tds, dsi8, recorded_at)
                 VALUES (%s, %s, %s, NOW())"""
        cur.execute(sql, (node_name, tds, dsi8))
        conn.commit()
        conn.close()
        print(f"✅ Logged Water Data for {node_name}")
    except Exception as e: print(f"❌ Water Log Error: {e}")

def log_hepa_data(node_name, aqi, ps):
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        sql = """INSERT INTO hepa_node_history (node_name, aqi, ps, recorded_at)
                 VALUES (%s, %s, %s, NOW())"""
        cur.execute(sql, (node_name, aqi, ps))
        conn.commit()
        conn.close()
        print(f"✅ Logged HEPA Data for {node_name}")
    except Exception as e: print(f"❌ HEPA Log Error: {e}")

# --- MOCK DATA GENERATOR ---
def populate_dummy_history(user_email):
    """Generates 7 days of fake history for ALL node types belonging to user."""
    conn = get_db_conn()
    cur = conn.cursor()
    print(f"🔄 Generating mock data for user: {user_email}")

    # 1. AIR NODES
    cur.execute("SELECT air_node_name FROM air_node WHERE avaliable_to_connect = %s", (user_email,))
    air_nodes = cur.fetchall()
    for node in air_nodes:
        name = node[0]
        for i in range(7):
            date = datetime.now() - timedelta(days=(6-i))
            sql = """INSERT INTO air_node_history (node_name, mq135, mq7, mq2, mq4, mq6, temp, humidity, recorded_at)
                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            cur.execute(sql, (name, random.randint(800, 1600), random.randint(100, 500),
                              random.randint(200, 800), random.randint(150, 600), random.randint(100, 400),
                              random.uniform(22.0, 32.0), random.uniform(40.0, 70.0), date))
        print(f"   -> Added history for Air Node: {name}")

    # 2. WATER NODES
    cur.execute("SELECT water_node_name FROM water_node WHERE avaliable_to_connect = %s", (user_email,))
    water_nodes = cur.fetchall()
    for node in water_nodes:
        name = node[0]
        for i in range(7):
            date = datetime.now() - timedelta(days=(6-i))
            sql = """INSERT INTO water_node_history (node_name, tds, dsi8, recorded_at)
                     VALUES (%s, %s, %s, %s)"""
            cur.execute(sql, (name, random.randint(50, 400), random.uniform(20.0, 28.0), date))
        print(f"   -> Added history for Water Node: {name}")

    # 3. HEPA NODES
    cur.execute("SELECT hepa_node_name FROM hepa_node WHERE avaliable_to_connect = %s", (user_email,))
    hepa_nodes = cur.fetchall()
    for node in hepa_nodes:
        name = node[0]
        for i in range(7):
            date = datetime.now() - timedelta(days=(6-i))
            # Simulate HEPA data
            aqi_val = random.randint(10, 80)
            ps_val = "Good" if aqi_val < 50 else "Moderate"
            sql = """INSERT INTO hepa_node_history (node_name, aqi, ps, recorded_at)
                     VALUES (%s, %s, %s, %s)"""
            cur.execute(sql, (name, aqi_val, ps_val, date))
        print(f"   -> Added history for HEPA Node: {name}")

    conn.commit()
    cur.close()
    conn.close()
    print("✅ Mock Data Generation Complete.")

def fetch_email_and_pass_for_login(user_email):
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT username, email, password FROM users WHERE email=%s", (user_email,))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows
    except Exception as e:
        print("DB fetch error:", e)
        return []

def upload_user_details(username, email, password):
    try:
        conn = get_db_conn()
        cur = conn.cursor()

        cur.execute("""INSERT INTO users (username, email, password, gender, dob, profile_pic, if_profile, state, city) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""", (username, email, password, 'male', '12-10-2009', '09', 'no', 'Tamil Nadu', 'Chennai'))

        conn.commit()
        cur.close()
        conn.close()

        print(f"User uploaded: {username}")
        return True

    except Exception as e:
        print("DB upload error:", e)
        return False

def get_all_names_air_nodes_online():
    connection = psycopg2.connect(host=host, database=database, user=user, password=password, port=port)
    conn = connection.cursor()

    conn.execute("SELECT air_node_name FROM air_node;")
    data = conn.fetchall()

    conn.close()
    connection.close()
    return data

def update_air_node_activity_online(node_name, is_act):
    connection = psycopg2.connect(host=host, database=database, user=user, password=password, port=port)
    conn = connection.cursor()

    conn.execute(f"""UPDATE air_node SET activity_status='{is_act}' WHERE air_node_name='{node_name}';""")

    connection.commit()
    conn.close()
    connection.close()

def get_email_for_air_node(client_id):
    connection = psycopg2.connect(host=host, database=database, user=user, password=password, port=port)
    conn = connection.cursor()

    conn.execute(f"SELECT avaliable_to_connect FROM air_node WHERE air_node_name='{client_id}';")
    data = conn.fetchall()
    try:
        if data[0] == 'False':
            return False
        else:
            return data[0]
    except:
        return False

def add_air_node_online(name, password123, mq135, mq7, mq2, mq4, mq6, dht22_hum, dht22_temp, activity_status, bat_status, available_to_connect):
    connection = psycopg2.connect(host=host, database=database, user=user, password=password, port=port)
    conn = connection.cursor()

    conn.execute(f"""
        INSERT INTO air_node
        VALUES(
            '{name}',
            '{password123}',
            '{mq135}',
            '{mq7}',
            '{mq2}',
            '{mq4}',
            '{mq6}',
            '{dht22_hum}',
            '{dht22_temp}',
            '{activity_status}',
            '{bat_status}',
            '{available_to_connect}'
        );
    """)

    connection.commit()
    conn.close()
    connection.close()

def update_air_node_online(name, mq135, mq7, mq2, mq4, mq6, dht22_hum, dht22_temp, activity_status, bat_status):
    connection = psycopg2.connect(host=host, database=database, user=user, password=password, port=port)
    conn = connection.cursor()

    conn.execute(f"""UPDATE air_node SET mq135='{mq135}', mq7='{mq7}', mq2='{mq2}', mq4='{mq4}', mq6='{mq6}', dht22_hum='{dht22_hum}', dht22_temp='{dht22_temp}', activity_status='{activity_status}', bat_status='{bat_status}' WHERE air_node_name = '{name}';""")

    connection.commit()
    conn.close()
    connection.close()

def check_air_node_add_to_app(air_node, pwd):
    connection = psycopg2.connect(host=host, database=database, user=user, password=password, port=port)
    conn = connection.cursor()

    conn.execute(f"SELECT password FROM air_node WHERE air_node_name='{air_node}';")
    data = conn.fetchall()
    try:
        if data[0][0] == pwd:
            return True
        else:
            return False
    except:
        return False

def get_data_air_node_online(node_id):
    connection = psycopg2.connect(host=host, database=database, user=user, password=password, port=port)
    conn = connection.cursor()

    conn.execute(f"""SELECT mq135, mq7, mq2, mq4, mq6, dht22_hum, dht22_temp, activity_status, bat_status FROM air_node WHERE air_node_name='{node_id}';""")
    data = conn.fetchone()

    conn.close()
    connection.close()

    # returns: [mq135, mq7, mq2, mq4, mq6, hum, temp, activity_status, bat_status]
    return list(data) if data else []

def get_all_names_water_nodes_online():
    connection = psycopg2.connect(host=host, database=database, user=user, password=password, port=port)
    conn = connection.cursor()

    conn.execute(f"SELECT water_node_name FROM water_node;")
    data = conn.fetchall()

    return data

def update_water_node_activity_online(node_name, is_act):
    connection = psycopg2.connect(host=host, database=database, user=user, password=password, port=port)
    conn = connection.cursor()

    conn.execute(f"""UPDATE water_node SET activity_status='{is_act}' WHERE water_node_name='{node_name}';""")

    connection.commit()

def add_water_node_online(name, password123, tds, dsi8, activity_status, bat_status, available_to_connect):
    connection = psycopg2.connect(host=host, database=database, user=user, password=password, port=port)
    conn = connection.cursor()

    conn.execute(f"""INSERT INTO water_node VALUES('{name}', '{password123}', '{tds}', '{dsi8}', '{activity_status}', '{bat_status}', '{available_to_connect}')""")

    connection.commit()

def update_water_node_online(name, tds, dsi8, activity_status, bat_status):
    connection = psycopg2.connect(host=host, database=database, user=user, password=password, port=port)
    conn = connection.cursor()

    conn.execute(f"""UPDATE water_node SET tds='{tds}', dsi8='{dsi8}', activity_status='{activity_status}', bat_status='{bat_status}' WHERE water_node_name='{name}';""")

    connection.commit()

def get_email_for_water_node(client_id):
    connection = psycopg2.connect(host=host, database=database, user=user, password=password, port=port)
    conn = connection.cursor()

    conn.execute(f"SELECT avaliable_to_connect FROM water_node WHERE water_node_name='{client_id}';")
    data = conn.fetchall()

    try:
        if data[0] == 'False':
            return False
        else:
            return data[0]
    except:
        return False

def check_water_node_add_to_app(water_node, pwd):
    connection = psycopg2.connect(host=host, database=database, user=user, password=password, port=port)
    conn = connection.cursor()

    conn.execute(f"SELECT password FROM water_node WHERE water_node_name='{water_node}';")
    data = conn.fetchall()
    try:
        if data[0][0] == pwd:
            return True
        else:
            return False
    except:
        return False

def get_data_water_node_online(node_id):
    connection = psycopg2.connect(host=host, database=database, user=user, password=password, port=port)
    conn = connection.cursor()

    conn.execute(f"""SELECT tds, dsi8, activity_status, bat_status FROM water_node WHERE water_node_name='{node_id}';""")
    data = conn.fetchone()
    return list(data)

def get_all_names_hepa_nodes_online():
    connection = psycopg2.connect(host=host, database=database, user=user, password=password, port=port)
    conn = connection.cursor()

    conn.execute(f"SELECT hepa_node_name FROM hepa_node;")
    data = conn.fetchall()

    return data

def update_hepa_node_activity_online(node_name, is_act):
    connection = psycopg2.connect(host=host, database=database, user=user, password=password, port=port)
    conn = connection.cursor()

    conn.execute(f"""UPDATE hepa_node SET activity_status='{is_act}' WHERE hepa_node_name='{node_name}';""")

    connection.commit()

def add_hepa_node_online(name, password123, aqi, ps, activity_status, bat_status, available_to_connect):
    connection = psycopg2.connect(host=host, database=database, user=user, password=password, port=port)
    conn = connection.cursor()

    conn.execute(f"""INSERT INTO hepa_node VALUES('{name}', '{password123}', '{aqi}', '{ps}', '{activity_status}', '{bat_status}', '{available_to_connect}')""")

    connection.commit()

def update_hepa_node_online(name, aqi, ps, activity_status, bat_status):
    connection = psycopg2.connect(host=host, database=database, user=user, password=password, port=port)
    conn = connection.cursor()

    conn.execute(f"""UPDATE hepa_node SET aqi='{aqi}', ps='{ps}', activity_status='{activity_status}', bat_status='{bat_status}' WHERE hepa_node_name='{name}';""")

    connection.commit()

def get_email_for_hepa_node(client_id):
    connection = psycopg2.connect(host=host, database=database, user=user, password=password, port=port)
    conn = connection.cursor()

    conn.execute(f"SELECT avaliable_to_connect FROM hepa_node WHERE hepa_node_name='{client_id}';")
    data = conn.fetchall()

    try:
        if data[0] == 'False':
            return False
        else:
            return data[0]
    except:
        return False

def check_hepa_node_add_to_app(hepa_node, pwd):
    connection = psycopg2.connect(host=host, database=database, user=user, password=password, port=port)
    conn = connection.cursor()

    conn.execute(f"SELECT password FROM hepa_node WHERE hepa_node_name='{hepa_node}';")
    data = conn.fetchall()
    try:
        if data[0][0] == pwd:
            return True
        else:
            return False
    except:
        return False

def get_data_hepa_node_online(node_id):
    connection = psycopg2.connect(host=host, database=database, user=user, password=password, port=port)
    conn = connection.cursor()

    conn.execute(f"""SELECT aqi, ps, activity_status, bat_status FROM hepa_node WHERE hepa_node_name='{node_id}';""")
    data = conn.fetchone()
    return list(data)

def add_genesis_node_online(name, password123, aqi, activity_status, bat_status, available_to_connect):
    """Add Genesis node to online database
    aqi: stored as string representation of list [input, output]
    """
    connection = psycopg2.connect(host=host, database=database, user=user, password=password, port=port)
    conn = connection.cursor()
    conn.execute(f"""
        INSERT INTO genesis_node (genesis_node_name, password, aqi, activity_status, bat_status, avaliable_to_connect, lux, ps)
        VALUES ('{name}', '{password123}', '{aqi}', '{activity_status}', '{bat_status}', '{available_to_connect}', '[NULL]', '[NULL]')
    """)
    connection.commit()
    conn.close()
    connection.close()

def update_genesis_node_online(name, aqi_input, aqi_output, lux, ps, activity_status, bat_status):
    """Update Genesis node data in online database
    Store aqi as list [input, output]
    """
    connection = psycopg2.connect(host=host, database=database, user=user, password=password, port=port)
    conn = connection.cursor()

    # Format AQI as list
    aqi_list = f"[{aqi_input},{aqi_output}]"

    conn.execute(f"""
        UPDATE genesis_node SET 
            aqi='{aqi_list}',
            lux='{lux}',
            ps='{ps}',
            activity_status='{activity_status}',
            bat_status='{bat_status}'
        WHERE genesis_node_name='{name}'
    """)
    connection.commit()
    conn.close()
    connection.close()

def get_data_genesis_node_online(node_id):
    """Get Genesis node data from online database"""
    connection = psycopg2.connect(host=host, database=database, user=user, password=password, port=port)
    conn = connection.cursor()
    conn.execute(f"""
        SELECT aqi, lux, ps, activity_status, bat_status 
        FROM genesis_node 
        WHERE genesis_node_name='{node_id}'
    """)
    data = conn.fetchone()
    conn.close()
    connection.close()

    if data:
        return list(data)
    else:
        return ["[0,0]", "0", "OFF", "False", "0"]

def get_all_names_genesis_nodes_online():
    """Get all Genesis node names from online database"""
    connection = psycopg2.connect(host=host, database=database, user=user, password=password, port=port)
    conn = connection.cursor()
    conn.execute("SELECT genesis_node_name FROM genesis_node")
    data = conn.fetchall()
    conn.close()
    connection.close()
    return data

def update_genesis_node_activity_online(node_name, is_act):
    """Update Genesis node activity status"""
    connection = psycopg2.connect(host=host, database=database, user=user, password=password, port=port)
    conn = connection.cursor()
    conn.execute(f"""
        UPDATE genesis_node 
        SET activity_status='{is_act}' 
        WHERE genesis_node_name='{node_name}'
    """)
    connection.commit()
    conn.close()
    connection.close()

def get_email_for_genesis_node(client_id):
    """Get email associated with Genesis node"""
    connection = psycopg2.connect(host=host, database=database, user=user, password=password, port=port)
    conn = connection.cursor()
    conn.execute(f"""
        SELECT avaliable_to_connect 
        FROM genesis_node 
        WHERE genesis_node_name='{client_id}'
    """)
    data = conn.fetchone()
    conn.close()
    connection.close()

    try:
        if data and data[0] and data[0] != 'False':
            return data[0]
        else:
            return None
    except:
        return None

def check_genesis_node_add_to_app(genesis_node, pwd):
    """Check if Genesis node password matches for adding to app"""
    connection = psycopg2.connect(host=host, database=database, user=user, password=password, port=port)
    conn = connection.cursor()
    conn.execute(f"""
        SELECT password 
        FROM genesis_node 
        WHERE genesis_node_name='{genesis_node}'
    """)
    data = conn.fetchone()
    conn.close()
    connection.close()

    try:
        if data and data[0] == pwd:
            return True
        else:
            return False
    except:
        return False

def get_all_genesis_nodes_data_bulk():
    """Fetch essential data for ALL Genesis nodes in one query"""
    try:
        connection = psycopg2.connect(host=host, database=database, user=user, password=password, port=port)
        conn = connection.cursor()
        conn.execute("SELECT genesis_node_name, aqi, activity_status FROM genesis_node")
        rows = conn.fetchall()
        conn.close()
        connection.close()
        return rows
    except Exception as e:
        print(f"Bulk Genesis Fetch Error: {e}")
        return []


# ================================
# GENESIS NODE HISTORY LOGGING
# ================================

def log_genesis_data(node_name, aqi_input, aqi_output, lux, ps):
    """Log Genesis node data to history table"""
    try:
        connection = psycopg2.connect(host=host, database=database, user=user, password=password, port=port)
        conn = connection.cursor()

        sql = """
            INSERT INTO genesis_node_history 
            (node_name, aqi_input, aqi_output, lux, ps, recorded_at) 
            VALUES (%s, %s, %s, %s, %s, NOW())
        """
        conn.execute(sql, (node_name, aqi_input, aqi_output, lux, ps))
        connection.commit()
        conn.close()
        connection.close()
        print(f"✓ Logged Genesis Data for {node_name}")
    except Exception as e:
        print(f"✗ Genesis Log Error: {e}")


def record_genesis_nodes_history():
    """Record hourly snapshot of all Genesis nodes"""
    try:
        connection = psycopg2.connect(host=host, database=database, user=user, password=password, port=port)
        conn = connection.cursor()

        # Get all genesis nodes
        conn.execute("SELECT genesis_node_name, aqi, lux, ps FROM genesis_node")
        nodes = conn.fetchall()

        # Insert history records
        for node in nodes:
            node_name, aqi, lux, ps = node

            # Parse AQI list [input, output]
            aqi_input = None
            aqi_output = None
            try:
                import ast
                if isinstance(aqi, str):
                    aqi_list = ast.literal_eval(aqi)
                    if isinstance(aqi_list, list) and len(aqi_list) >= 2:
                        aqi_input = aqi_list[0]
                        aqi_output = aqi_list[1]
            except:
                pass

            sql = """
                INSERT INTO genesis_node_history 
                (node_name, aqi_input, aqi_output, lux, ps, recorded_at) 
                VALUES (%s, %s, %s, %s, %s, NOW())
            """
            conn.execute(sql, (node_name, aqi_input, aqi_output, lux, ps))

        connection.commit()
        conn.close()
        connection.close()
        print(f"✅ Recorded history for {len(nodes)} Genesis nodes")

    except Exception as e:
        print(f"❌ Genesis history recording error: {e}")


def add_drone_online():
    connection = psycopg2.connect(host=host, database=database, user=user, password=password, port=port)
    conn = connection.cursor()

    conn.execute()

    connection.commit()

def update_drone_online():
    connection = psycopg2.connect(host=host, database=database, user=user, password=password, port=port)
    conn = connection.cursor()

    conn.execute()

    connection.commit()

def get_drone_online():
    connection = psycopg2.connect(host=host, database=database, user=user, password=password, port=port)
    conn = connection.cursor()

    conn.execute()

    connection.commit()

def get_ip_port_for_esp_upload_online():
    connection = psycopg2.connect(host=host, database=database, user=user, password=password, port=port)
    conn = connection.cursor()

    conn.execute()

    connection.commit()

AVAILABLE_THEMES = {"Pink": pink, "Lavender": lavender_og, "Blue": blue, "Green": green, "Orange": orange}

def load_selected_theme():
    if os.path.exists("gaia_settings.json"):
        with open("gaia_settings.json", "r") as f:
            name = json.load(f).get("theme", 'Lavender')
            return AVAILABLE_THEMES.get(name, 'Lavender')
    else:
        return lavender_og

THEME = load_selected_theme()

COLORS = {
    # Core backgrounds & accents
    "bg_primary": THEME["LAVENDER_MIST"],
    "bg_secondary": THEME["WISTERIA"],
    "accent": THEME["VELVET_ORCHID"],
    "accent_hover": THEME["DARK_AMETHYST"],
    "text_main": THEME["COFFEE_BEAN"],
    "text_subtle": THEME["VELVET_ORCHID"],
    "border": THEME["DARK_AMETHYST"],
    "shadow": THEME["COFFEE_BEAN"],

    # Status / system
    "danger": THEME["DANGER"],
    "danger_hover": THEME["DANGER_HOVER"],
    "success": THEME["SUCCESS"],

    # Generic backgrounds
    "bg": THEME["LAVENDER_MIST"],
    "accent1": THEME["WISTERIA"],
    "accent2": THEME["VELVET_ORCHID"],
    "accent3": THEME["DARK_AMETHYST"],
    "accent4": THEME["COFFEE_BEAN"],

    # Panels / cards
    "panel": THEME["PANEL"],
    "panel_edge": THEME["PANEL_EDGE"],
    "panel_alt": THEME["PANEL_ALT"],
    "text": THEME["PANEL_TEXT"],
    "subtext": THEME["PANEL_SUBTEXT"],

    # Warnings / selection
    "warn": THEME["WARN"],
    "warn_hover": THEME["WARN_HOVER"],
    "select": THEME["SELECT"],

    # Text / muted
    "text_dark": THEME["TEXT_DARK"],
    "muted": THEME["MUTED"],

    # Frames
    "frame": THEME["FRAME_BG"],

    # Root / sidebar
    "root_bg_dark": THEME["ROOT_BG_DARK"],
    "SIDEBAR_BG": THEME["SIDEBAR_BG"],
    "SIDEBAR_ACTIVE": THEME["SIDEBAR_ACTIVE"],
    "DIVIDER": THEME["DIVIDER"],
    "DANGER_HOVER": THEME["DANGER_HOVER"],
    "no_internet_bg": THEME["NO_INTERNET_BG"],

    # Progress / login / inputs
    "progress_bg": THEME["PROGRESS_BG"],
    "login_btn_bg": THEME["LOGIN_BTN_BG"],
    "login_btn_hover": THEME["LOGIN_BTN_HOVER"],
    "placeholder": THEME["PLACEHOLDER"],

    # Profile / clear hover
    "profile_bg": THEME["PROFILE_BG"],
    "clear_hover": THEME["CLEAR_HOVER"],

    # Status pills
    "status_online": THEME["STATUS_ONLINE"],
    "status_offline": THEME["STATUS_OFFLINE"],
}

def send_support_ticket(username, user_email, subject, category, description, attachment_path=None):
    def send_email(username1, user_email1, subject1, category1, description1, file_path):
        my_email = 'gaiasentinel@gmail.com'
        password_e = ''

        message = EmailMessage()
        message["subject"] = f"Gaia Sentinel - Support Ticket • {subject1}"
        message["from"] = "Gaia Sentinel - Support System"
        message["to"] = my_email

        html = f"""
<!doctype html>
<html>
<head>
    <meta charset="utf-8">
    <title>Gaia Sentinel — Support Ticket</title>
</head>
<body style="
    margin:0;
    padding:0;
    font-family:Arial,Helvetica,sans-serif;
    background:#F0EAFE;
    color:#2e241f;
">
    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
        <tr>
            <td align="center" style="padding:24px 12px;">
                <table role="presentation" cellspacing="0" cellpadding="0" border="0"
                       style="
                           max-width:600px;
                           width:100%;
                           background:#ffffff;
                           border-radius:18px;
                           box-shadow:0 10px 30px rgba(0,0,0,0.08);
                           overflow:hidden;
                           border:1px solid #eee;
                       ">
                    <!-- Header strip -->
                    <tr>
                        <td style="
                            padding:14px 22px;
                            background:linear-gradient(100deg, rgba(200,162,255,0.12), rgba(139,63,155,0.08));
                            border-bottom:1px solid #f0eef8;
                        ">
                            <div style="font-size:12px;color:#7b6f85;text-transform:uppercase;letter-spacing:1px;">
                                GAIA SENTINEL
                            </div>
                            <div style="font-size:18px;font-weight:bold;color:#8b3f9b;margin-top:2px;">
                                🛟 New Support Ticket
                            </div>
                        </td>
                    </tr>
                    <!-- Main content -->
                    <tr>
                        <td style="padding:22px 24px 8px 24px;">
                            <p style="margin:0 0 8px 0;font-size:15px;color:#2e241f;">
                                <strong>User:</strong> {username1}
                            </p>
                            <p style="margin:0 0 8px 0;font-size:15px;color:#2e241f;">
                                <strong>Email:</strong> {user_email1}
                            </p>
                            <p style="margin:0 0 16px 0;font-size:15px;color:#2e241f;">
                                <strong>Category:</strong>
                                <span style="
                                    display: inline-block;
                                    background: #f0eef8;
                                    color: #8b3f9b;
                                    padding: 4px 10px;
                                    border-radius: 12px;
                                    font-size: 13px;
                                    margin-left: 5px;
                                    font-weight: 500;
                                ">
                                    {category1}
                                </span>
                            </p>
                            <!-- Description pill -->
                            <div style="
                                background:#f8f2ff;
                                border-left:5px solid #8b3f9b;
                                padding:14px;
                                border-radius:8px;
                                color:#3c2f35;
                                font-size:15px;
                                line-height:1.5;
                                margin-bottom: 18px;
                            ">
                                {description1}
                            </div>
                            <!-- Divider -->
                            <hr style="border:none;border-top:1px solid #f0eef8;margin:18px 0 12px 0;">
                            <!-- Security notes -->
                            <p style="margin:0 0 4px 0;font-size:12px;color:#7b6f85;">
                                📧 This ticket was submitted automatically via Gaia Sentinel Support Panel.
                            </p>
                        </td>
                    </tr>
                    <!-- Footer -->
                    <tr>
                        <td style="
                            padding:16px 24px 20px 24px;
                            background:#fbfbff;
                            border-top:1px solid #f0eef8;
                        ">
                            <p style="margin:0 0 4px 0;font-size:11px;color:#7f8083;">
                                © Gaia Sentinel — Protecting nature together.
                            </p>
                            <p style="margin:0;font-size:11px;color:#7f8083;">
                                This is an automated message. Please don’t reply to this email.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""


        message.set_content(f"User: {username1}\nCategory: {category1}\n\n{description1}")
        message.add_alternative(html, subtype="html")

        if file_path:
            mime_type, _ = mimetypes.guess_type(file_path)
            if mime_type:
                mime_main, mime_sub = mime_type.split("/")
            else:
                mime_main, mime_sub = "application", "octet-stream"

            with open(file_path, "rb") as f:
                message.add_attachment(f.read(), maintype=mime_main, subtype=mime_sub, filename=os.path.basename(file_path))

        try:
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(my_email, password_e)
            server.send_message(message)
            server.quit()
        except Exception:
            pass

    th = threading.Thread(target=send_email, args=(username, user_email, subject, category, description, attachment_path))
    th.start()

def send_mail_for_otp(username: str, email: str, otp: str, valid_minutes: int = 10) -> None:
    SENDER_EMAIL = 'gaiasentinel@gmail.com'
    SENDER_PASSWORD = ''
    SUPPORT_NAME = "Gaia Sentinel Team"

    if not SENDER_EMAIL or not SENDER_PASSWORD:
        print("send_mail_for_otp: email credentials not set (GAIA_EMAIL / GAIA_EMAIL_PASSWORD). Skipping send.")
        return

    def _worker(username_inner: str, to_email: str, otp_inner: str, minutes: int):
        try:
            msg = EmailMessage()
            msg["Subject"] = "Gaia Sentinel — OTP Verification"
            msg["From"] = f"{SUPPORT_NAME} <{SENDER_EMAIL}>"
            msg["To"] = to_email

            plaintext = f"Hello {username_inner},\n\nYour One-Time Passcode (OTP) is: {otp_inner}\n\nThis code is valid for {minutes} minutes. If you did not request this, please ignore this message.\n\n— {SUPPORT_NAME}"
            html = f"""\
<!doctype html>
<html>
<head>
    <meta charset="utf-8">
    <title>Gaia Sentinel — OTP</title>
</head>
<body style="
    margin:0;
    padding:0;
    font-family:Arial,Helvetica,sans-serif;
    background:#F0EAFE;
    color:{COLORS['text_dark']};
">
    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
        <tr>
            <td align="center" style="padding:24px 12px;">
                <table role="presentation" cellspacing="0" cellpadding="0" border="0" 
                       style="
                           max-width:600px;
                           width:100%;
                           background:#ffffff;
                           border-radius:18px;
                           box-shadow:0 10px 30px rgba(0,0,0,0.08);
                           overflow:hidden;
                           border:1px solid {COLORS['border']};
                       ">
                    <!-- Header strip -->
                    <tr>
                        <td style="
                            padding:14px 22px;
                            background:{COLORS['accent1']};
                            border-bottom:1px solid {COLORS['panel_edge']};
                        ">
                            <div style="font-size:12px;color:{COLORS['text_subtle']};text-transform:uppercase;letter-spacing:1px;">
                                GAIA SENTINEL
                            </div>
                            <div style="font-size:18px;font-weight:bold;color:{COLORS['text_main']};margin-top:2px;">
                                One‑Time Passcode
                            </div>
                        </td>
                    </tr>

                    <!-- Main content -->
                    <tr>
                        <td style="padding:22px 24px 8px 24px;">
                            <p style="margin:0 0 8px 0;font-size:15px;color:{COLORS['text_dark']};">
                                Hi <strong>{username_inner}</strong>,
                            </p>
                            <p style="margin:0 0 16px 0;font-size:14px;color:{COLORS['subtext']};line-height:1.5;">
                                Use the OTP below to complete your sign‑in to 
                                <strong>Gaia Sentinel</strong>. For your security, please don’t share this code with anyone.
                            </p>

                            <!-- OTP pill -->
                            <div style="
                                text-align:center;
                                margin:20px auto 8px auto;
                            ">
                                <div style="
                                    display:inline-block;
                                    padding:14px 24px;
                                    border-radius:999px;
                                    background:{COLORS['accent2']};
                                    color:#ffffff;
                                    font-size:28px;
                                    font-weight:700;
                                    letter-spacing:8px;
                                    box-shadow:0 8px 18px rgba(0,0,0,0.15);
                                ">
                                    {otp_inner}
                                </div>
                            </div>

                            <!-- Validity + info -->
                            <p style="margin:10px 0 4px 0;font-size:13px;color:{COLORS['text_subtle']};text-align:center;">
                                This code will expire in <strong>{minutes} minutes</strong>.
                            </p>
                            <p style="margin:0 0 18px 0;font-size:12px;color:{COLORS['muted']};text-align:center;">
                                If you didn’t request this code, you can safely ignore this email.
                            </p>

                            <!-- Divider -->
                            <hr style="border:none;border-top:1px solid {COLORS['panel_edge']};margin:18px 0 12px 0;">

                            <!-- Security notes -->
                            <p style="margin:0 0 4px 0;font-size:12px;color:{COLORS['subtext']};">
                                🔒 <strong>Security tip:</strong> Gaia Sentinel will never ask you to share this code in chat or over a call.
                            </p>
                            <p style="margin:0;font-size:12px;color:{COLORS['subtext']};">
                                🌍 You’re receiving this message because an OTP was requested for your Gaia Sentinel account.
                            </p>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="
                            padding:16px 24px 20px 24px;
                            background:{COLORS['panel']};
                            border-top:1px solid {COLORS['panel_edge']};
                        ">
                            <p style="margin:0 0 4px 0;font-size:11px;color:{COLORS['muted']};">
                                © Gaia Sentinel — Protecting nature together.
                            </p>
                            <p style="margin:0;font-size:11px;color:{COLORS['muted']};">
                                This is an automated message. Please don’t reply to this email.
                            </p>
                        </td>
                    </tr>

                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""

            msg.set_content(plaintext)
            msg.add_alternative(html, subtype="html")

            with smtplib.SMTP("smtp.gmail.com", 587, timeout=20) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(SENDER_EMAIL, SENDER_PASSWORD)
                server.send_message(msg)

            print(f"OTP email sent to {to_email}")
        except Exception as ex:
            print("Error sending OTP email:", ex)

    th = threading.Thread(target=_worker, args=(username, email, otp, valid_minutes), daemon=True)
    th.start()

def send_node_credentials(username: str, to_email: str, node_id: str, node_password: str, node_type: str) -> None:
    SENDER_EMAIL = "gaiasentinel@gmail.com"
    SENDER_PASSWORD = ""
    SUPPORT_NAME = "Gaia Sentinel Team"
    SUPPORT_EMAIL = "gaiasentinel@gmail.com"

    if not SENDER_EMAIL or not SENDER_PASSWORD:
        print("send_node_credentials: email credentials not set. Skipping send.")
        return

    def worker(username_inner: str, to_email_inner: str, node_id_inner: str, node_password_inner: str, node_type_inner: str) -> None:
        try:
            msg = EmailMessage()
            msg["Subject"] = f"Gaia Sentinel — {node_type_inner} Node Credentials"
            msg["From"] = f"{SUPPORT_NAME} <{SENDER_EMAIL}>"
            msg["To"] = to_email_inner

            # ---------- Plain text ----------
            plaintext = (
                f"Hello {username_inner},\n\n"
                f"Your {node_type_inner} node has been provisioned.\n\n"
                f"Node ID: {node_id_inner}\n"
                f"Node Password: {node_password_inner}\n\n"
                "Instructions:\n"
                "- Connect the node to Wi-Fi using the configured SSID & password.\n"
                "- The node will report to the Gaia Sentinel server automatically.\n\n"
                f"If you need help, contact {SUPPORT_EMAIL}.\n\n"
                "— Gaia Sentinel Team")

            year = datetime.datetime.now().year
            html = f"""<!doctype html>
            <html>
            <head>
              <meta charset="utf-8">
              <meta name="viewport" content="width=device-width, initial-scale=1">
              <title>Gaia Sentinel — Node Credentials</title>
              <style>
                @media only screen and (max-width: 600px){{
                  .gs-container {{
                    width: 100% !important;
                    border-radius: 14px !important;
                  }}
                  .gs-body {{
                    padding: 18px !important;
                  }}
                  .gs-header-title {{
                    font-size: 20px !important;
                  }}
                  .gs-hello {{
                    font-size: 15px !important;
                  }}
                  .gs-text {{
                    font-size: 13px !important;
                  }}
                  .gs-cred-box {{
                    padding: 12px 14px !important;
                  }}
                }}
              </style>
            </head>
            <body style="margin:0;padding:0;background:#F0EAFE;font-family:Arial,Helvetica,sans-serif;">

            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="min-width:320px;">
              <tr>
                <td align="center" style="padding:24px 10px;">

                  <!-- Outer card -->
                  <table role="presentation" cellpadding="0" cellspacing="0"
                         class="gs-container"
                         style="
                           width:700px;
                           max-width:700px;
                           background:#ffffff;
                           border-radius:18px;
                           overflow:hidden;
                           border:1px solid {COLORS['panel_edge']};
                           box-shadow:0 12px 30px rgba(0,0,0,0.06);
                         ">

                    <!-- Header strip -->
                    <tr>
                      <td style="
                            padding:16px 24px 12px 24px;
                            background:{COLORS['accent1']};
                            border-bottom:1px solid {COLORS['panel_edge']};
                          ">
                        <div style="
                              font-size:12px;
                              letter-spacing:1px;
                              text-transform:uppercase;
                              color:{COLORS['text_subtle']};
                            ">
                          GAIA SENTINEL
                        </div>
                        <div class="gs-header-title" style="
                              margin-top:4px;
                              font-size:22px;
                              font-weight:700;
                              color:{COLORS['text_main']};
                            ">
                          Node Credentials
                        </div>
                      </td>
                    </tr>

                    <!-- Body -->
                    <tr>
                      <td class="gs-body" style="padding:24px 28px 16px 28px;">

                        <p class="gs-hello" style="margin:0 0 10px 0;font-size:16px;color:{COLORS['text_main']};">
                          Hello <strong>{username_inner}</strong>,
                        </p>

                        <p class="gs-text" style="margin:0 0 18px 0;font-size:14px;line-height:1.6;color:{COLORS['subtext']};">
                          Your device has been successfully registered with the Gaia Sentinel network.
                          Keep the credentials below secure — they are required for authentication.
                        </p>

                        <!-- Credentials pill box -->
                        <div style="
                              margin:6px 0 18px 0;
                              background:#F4EEFF;
                              border-radius:16px;
                              padding:0;
                            ">
                          <div style="
                                border-left:4px solid {COLORS['accent2']};
                                border-radius:16px;
                                padding:14px 18px;
                              " class="gs-cred-box">
                            <p style="margin:0 0 6px 0;font-size:14px;color:{COLORS['text_main']};">
                              <strong>Node Type:</strong> {node_type_inner}
                            </p>
                            <p style="margin:0 0 6px 0;font-size:14px;color:{COLORS['text_main']};">
                              <strong>Node ID:</strong>
                              <a href="#" style="color:{COLORS['accent2']};text-decoration:none;font-family:monospace;font-weight:700;">
                                {node_id_inner}
                              </a>
                            </p>
                            <p style="margin:0;font-size:14px;color:{COLORS['text_main']};">
                              <strong>Password:</strong>
                              <span style="font-family:monospace;font-weight:700;">
                                {node_password_inner}
                              </span>
                            </p>
                          </div>
                        </div>

                        <p class="gs-text" style="margin:0 0 14px 0;font-size:13px;color:{COLORS['subtext']};">
                          For help, contact
                          <a href="mailto:{SUPPORT_EMAIL}"
                             style="color:{COLORS['accent2']};text-decoration:none;font-weight:600;">
                            {SUPPORT_EMAIL}
                          </a>.
                        </p>

                        <div style="margin:18px 0 12px 0;border-top:1px solid {COLORS['panel_edge']};"></div>

                        <!-- Tips -->
                        <p class="gs-text" style="margin:0 0 6px 0;font-size:12px;color:{COLORS['warn']};">
                          🔒 <strong>Security tip:</strong> Never share your node ID or password publicly.
                        </p>
                        <p class="gs-text" style="margin:4px 0 0 0;font-size:12px;color:{COLORS['muted']};">
                          🌍 You're receiving this message because a node was configured under your account.
                        </p>

                      </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                      <td style="
                            padding:14px 26px 18px 26px;
                            text-align:center;
                            background:{COLORS['panel']};
                            border-top:1px solid {COLORS['panel_edge']};
                            font-size:12px;
                            color:{COLORS['muted']};
                          ">
                        © {year} Gaia Sentinel — Protecting nature together 🌍<br>
                        <span style="font-size:11px;">This is an automated message. Please don’t reply to this email.</span>
                      </td>
                    </tr>

                  </table>
                  <!-- /Outer card -->

                </td>
              </tr>
            </table>

            </body>
            </html>"""

            msg.set_content(plaintext)
            msg.add_alternative(html, subtype="html")

            with smtplib.SMTP("smtp.gmail.com", 587, timeout=20) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(SENDER_EMAIL, SENDER_PASSWORD)
                server.send_message(msg)

            print(f"Node credentials email sent to {to_email_inner} (node: {node_id_inner})")

        except Exception as ex:
            print("Error sending node credentials email:", ex)

    th = threading.Thread( target=worker, args=(username, to_email, node_id, node_password, node_type), daemon=True)
    th.start()

def send_mail_for_alert(to_email: str, node_id: str, node_type: str, risk_level: str, reasons: list[str]) -> None:
    SENDER_EMAIL = "gaiasentinel@gmail.com"
    SENDER_PASSWORD = ""
    SUPPORT_NAME = "Gaia Sentinel Team"

    if not SENDER_EMAIL or not SENDER_PASSWORD:
        print("send_mail_for_alert: email credentials not set. Skipping send.")
        return
    if not to_email:
        print("send_mail_for_alert: target email empty. Skipping send.")
        return

    def worker(to_email_inner: str, node_id_inner: str, node_type_inner: str, risk_level_inner: str, reasons_inner: list[str]) -> None:
        try:
            # --------- visual bits based on risk level ----------
            level_label = {
                "LOW": "Low risk",
                "MEDIUM": "Medium risk",
                "HIGH": "High / Critical",
            }.get(risk_level_inner, risk_level_inner)

            level_emoji = {
                "LOW": "🟡",
                "MEDIUM": "🟠",
                "HIGH": "🔴",
            }.get(risk_level_inner, "⚠️")

            badge_bg = {
                "LOW": COLORS["warn"],
                "MEDIUM": COLORS["accent2"],
                "HIGH": COLORS["danger"],
            }.get(risk_level_inner, COLORS["accent2"])

            badge_text = "#ffffff"

            subject = (
                f"Gaia Sentinel — {node_type_inner} node "
                f"{node_id_inner} {risk_level_inner} alert"
            )

            # ---------- plain‑text fallback ----------
            plaintext = (
                "Gaia Sentinel alert\n\n"
                f"Node: {node_id_inner} ({node_type_inner})\n"
                f"Alert level: {risk_level_inner}\n\n"
                "Reasons:\n- " + "\n- ".join(reasons_inner) + "\n\n"
                "Open Gaia Sentinel to view live status and history.\n"
            )

            reasons_html = "".join(f"<li>{r}</li>" for r in reasons_inner)
            year = datetime.datetime.now().year

            # ---------- HTML (responsive, mobile friendly) ----------
            html = html = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>{subject}</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>
    @media only screen and (max-width: 600px){{
      .gs-container {{
        width: 100% !important;
        border-radius: 14px !important;
      }}
      .gs-body {{
        padding: 18px !important;
      }}
      .gs-header-title {{
        font-size: 18px !important;
      }}
      .gs-text {{
        font-size: 13px !important;
      }}
      .gs-badge {{
        font-size: 11px !important;
        padding: 5px 10px !important;
      }}
    }}
  </style>
</head>
<body style="margin:0;padding:0;background:#F2EAFE;
             font-family:Arial,Helvetica,sans-serif;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="min-width:320px;">
  <tr>
    <td align="center" style="padding:24px 10px;">

      <!-- Card -->
      <table role="presentation" cellpadding="0" cellspacing="0"
             class="gs-container"
             style="width:100%;max-width:640px;background:#ffffff;
                    border-radius:18px;overflow:hidden;
                    border:1px solid {COLORS['panel_edge']};
                    box-shadow:0 10px 28px rgba(0,0,0,0.08);">

        <!-- Header -->
        <tr>
          <td style="padding:16px 22px;
                     background:{COLORS['accent1']};
                     border-bottom:1px solid {COLORS['panel_edge']};">
            <div style="font-size:12px;letter-spacing:1px;text-transform:uppercase;
                        color:{COLORS['text_subtle']};">
              GAIA SENTINEL
            </div>
            <div class="gs-header-title"
                 style="margin-top:4px;font-size:20px;font-weight:700;
                        color:{COLORS['text_main']};">
              {node_type} node alert
            </div>
          </td>
        </tr>

        <!-- Body -->
        <tr>
          <td class="gs-body"
              style="padding:20px 24px;font-size:14px;color:{COLORS['text_main']};">

            <p class="gs-text" style="margin:0 0 8px 0;">
              {level_emoji}
              <strong>{level_label}</strong> for node
              <strong>{node_id}</strong>.
            </p>

            <!-- Badge -->
            <div style="margin:12px 0 16px 0;">
              <span class="gs-badge"
                    style="display:inline-block;padding:6px 12px;
                           border-radius:999px;
                           background:{badge_bg};
                           color:{badge_text};
                           font-size:12px;font-weight:700;
                           letter-spacing:0.5px;text-transform:uppercase;">
                {risk_level} LEVEL • {node_type} NODE
              </span>
            </div>

            <p class="gs-text"
               style="margin:0 0 6px 0;color:{COLORS['text_main']};">
              The node has reported readings that crossed your configured
              safety thresholds. Summary:
            </p>

            <ul class="gs-text"
                style="margin:8px 0 14px 18px;padding:0;color:{COLORS['text_main']};">
              {reasons_html}
            </ul>

            <p class="gs-text"
               style="margin:0 0 16px 0;font-size:12px;color:{COLORS['muted']};">
              Open the <strong>Gaia Sentinel</strong> dashboard to see live
              graphs, history, and recommended actions.
            </p>

            <hr style="border:none;border-top:1px solid {COLORS['panel_edge']};
                       margin:16px 0 12px 0;">

            <p class="gs-text"
               style="margin:0 0 4px 0;font-size:12px;color:{COLORS['subtext']};">
              🔐 <strong>Security tip:</strong> Do not share your node
              credentials or raw sensor data in public channels.
            </p>
            <p class="gs-text"
               style="margin:4px 0 0 0;font-size:12px;color:{COLORS['muted']};">
              🌍 You’re receiving this alert because this node is linked to
              your Gaia Sentinel account.
            </p>

          </td>
        </tr>

        <!-- Footer -->
        <tr>
          <td style="padding:12px 22px;text-align:center;
                     background:{COLORS['panel']};
                     border-top:1px solid {COLORS['panel_edge']};
                     font-size:11px;color:{COLORS['muted']};">
            © {year} Gaia Sentinel — Protecting nature together.<br>
            This is an automated message. Please don’t reply to this email.
          </td>
        </tr>

      </table>
      <!-- /Card -->

    </td>
  </tr>
</table>
</body>
</html>"""

            msg = EmailMessage()
            msg["Subject"] = subject
            msg["From"] = f"{SUPPORT_NAME} <{SENDER_EMAIL}>"
            msg["To"] = to_email_inner
            msg.set_content(plaintext)
            msg.add_alternative(html, subtype="html")

            with smtplib.SMTP("smtp.gmail.com", 587, timeout=20) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(SENDER_EMAIL, SENDER_PASSWORD)
                server.send_message(msg)

            print(
                f"Alert email sent to {to_email_inner} "
                f"(node: {node_id_inner}, level: {risk_level_inner})"
            )
        except Exception as ex:
            print("Error sending alert email:", ex)

    th = threading.Thread(
        target=worker,
        args=(to_email, node_id, node_type, risk_level, reasons),
        daemon=True,
    )
    th.start()

