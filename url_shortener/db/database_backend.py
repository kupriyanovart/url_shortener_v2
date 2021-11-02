import sqlite3
from sqlite3 import OperationalError, IntegrityError, ProgrammingError


import settings


def connect_to_db(db=None):
    if db is None:
        db_name = ":memory:"
    else:
        db_name = "{}.db".format(db)
    connection = sqlite3.connect(db_name)
    return connection


# http://www.kylev.com/2009/05/22/python-decorators-and-database-idioms/
def connect(func):
    def inner_func(conn, *args, **kwargs):
        try:
            # I don't know if this is the simplest and fastest query to try
            conn.execute('SELECT name FROM sqlite_temp_master WHERE type="table";')
        except (AttributeError, ProgrammingError):
            conn = connect_to_db(settings.DB_NAME)
        return func(conn, *args, **kwargs)
    return inner_func


def disconnect_from_db(db=None, conn=None):
    if db is not settings.DB_NAME:
        print("You are trying to disconnect from a wrong DB")
    if conn:
        conn.close()


def scrub(input_string):
    """Clean an input string (to prevent SQL injection).

    Parameters
    ----------
    input_string : str

    Returns
    -------
    str
    """
    return "".join(k for k in input_string if k.isalnum() or k == "_")


@connect
def create_table(conn, table_name):
    table_name = scrub(table_name)
    sql = "CREATE TABLE IF NOT EXISTS {} (id INTEGER PRIMARY KEY AUTOINCREMENT," \
          "url TEXT UNIQUE, short_url TEXT UNIQUE)".format(table_name)
    try:
        conn.execute(sql)
    except OperationalError as e:
        print(e)


@connect
def insert_one(conn, *args, table_name):
    table_name = scrub(table_name)
    sql = "INSERT INTO {} ('url', 'short_url') VALUES (?, ?)".format(table_name)
    try:
        conn.execute(sql, args)
        conn.commit()
    except IntegrityError as e:
        print("already stored in table", e)


@connect
def select_one(conn, *args, table_name, **kwargs):
    table_name = scrub(table_name)
    sql = f"SELECT * FROM {table_name}"
    if kwargs:
        sql += " " + "WHERE"
        fl = True
        for key, value in kwargs.items():
            if fl:
                key = scrub(key)
                value = scrub(value)
                sql += " " + f"{key}" + "=" + f"'{value}'"
            else:
                key = scrub(key)
                value = scrub(value)
                sql += " " + "AND" + " " + f"{key}" + '=' + f"'{value}'"

    c = conn.execute(sql)
    result = c.fetchone()

    if result:
        result_dict = dict()
        result_dict["url"] = result[1]
        result_dict["short_url"] = result[2]
        return result_dict

    else:
        raise sqlite3.Error()
