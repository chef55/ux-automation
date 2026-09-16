import psycopg2
#returns record key
def push(data):
    conn = psycopg2.connect("dbname=website_db user=postgres password=50bmg")
    cur = conn.cursor()
    cur.execute('INSERT INTO image_table ("scenarioId", content) VALUES (%s, %s) RETURNING image_id;', (data["scenario_id"], data["content"]))
    conn.commit()
    return list(cur.fetchone())[0]