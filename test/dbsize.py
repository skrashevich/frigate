import sqlite3
import sys


def get_size_of_db(dbname):
    conn = sqlite3.connect(dbname)
    c = conn.cursor()

    # Get the names of all the tables in the database
    c.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = c.fetchall()

    for table in tables:
        print("Table: ", table[0])
        c.execute("PRAGMA table_info({})".format(table[0]))

        # Find total size of all rows and size of single row
        rows = c.fetchall()
        total_size = 0
        total_row = 0
        for row in rows:
            c.execute("SELECT COUNT({}) FROM {}".format(row[1], table[0]))
            num_rows = c.fetchone()[0]
            total_row += num_rows
            c.execute("SELECT AVG(LENGTH({})) FROM {}".format(row[1], table[0]))
            avg_length = c.fetchone()[0]
            if avg_length is None:
                avg_length = 0
            total_size += num_rows * avg_length

        print("Number of rows:", total_row)
        print("Estimated size (mbytes):", round(total_size / 1024 / 1024), "MB")
        print()

    conn.close()


get_size_of_db("../frigate.db")
