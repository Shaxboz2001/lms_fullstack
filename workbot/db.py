import psycopg2


def save_to_db(jobs):
    conn = psycopg2.connect(
        dbname="jobs_db", user="postgres", password="2001", host="localhost"
    )
    cur = conn.cursor()
    for title, location, url in jobs:
        cur.execute("""
            INSERT INTO jobs (source, title, location, url)
            VALUES (%s, %s, %s, %s)
        """, ('olx', title, location, url))
    conn.commit()
    cur.close()
    conn.close()
