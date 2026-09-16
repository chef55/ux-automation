import psycopg2
#returns record key
def push(data):
    conn = psycopg2.connect("dbname=website_db user=postgres password=50bmg")
    cur = conn.cursor()
    s, ms = divmod(data["ct"],1000)
    m, s = divmod(s,60)
    cur.execute('INSERT INTO scenario_table (keywords, eit, tei, ct, "testId") VALUES (%s, %s, %s, %s, %s) RETURNING scenario_id;', (data["keywords"], data["eit"], data["tei"], f"0:{int(m)}:{int(s)}.{int(ms)}", data["test_id"]))
    conn.commit()
    return list(cur.fetchone())[0]