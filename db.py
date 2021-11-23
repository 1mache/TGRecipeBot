import sqlite3

conn = sqlite3.connect(":memory:")
c = conn.cursor()

c.execute("""CREATE TABLE users(
    chat_id integer,
    plan_day text
    )""")

c.execute("""INSERT INTO users VALUES(1,"Friday")""")

conn.commit()

c.execute("""SELECT * FROM users""")

print (c.fetchone())