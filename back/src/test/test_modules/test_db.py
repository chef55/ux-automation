import psycopg2
#returns record key
def push(data):
    conn = psycopg2.connect("dbname=website_db user=admin password=admin")
    cur = conn.cursor()
    cur.execute('INSERT INTO scenario_table (code, iet, tei, ct, "testId") VALUES (%s, %s, %s, %s, %s)', (data["code"], data["iet"], data["tei"], data["ct"], data["test_id"]))
    return list(cur.fetchone())[0]