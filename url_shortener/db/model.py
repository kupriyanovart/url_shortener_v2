import sqlite3

from . import database_backend
import settings


class Url:
    def __init__(self):
        self._table_name = "url"
        self._connection = database_backend.connect_to_db(settings.DB_NAME)
        database_backend.create_table(self.connection, self._table_name)

    @property
    def connection(self):
        return self._connection

    @property
    def item_type(self):
        return self._table_name

    @item_type.setter
    def item_type(self, new_table_name):
        self._table_name = new_table_name

    def create_item(self, url, short_url):
        database_backend.insert_one(
            self.connection, url, short_url, table_name=self.item_type)

    def read_item(self, *args, **kwargs):
        return database_backend.select_one(self.connection, *args, table_name=self.item_type, **kwargs)


