from playhouse.sqliteq import SqliteQueueDatabase
from peewee import SENTINEL
import time
import logging

logger = logging.getLogger(__name__)

class TimedSqliteQueueDatabase(SqliteQueueDatabase):
    def execute_sql(self, sql, params=None, commit=SENTINEL, timeout=None):
        start_time = time.time()
        cursor = super().execute_sql(sql, params, commit, timeout)
        end_time = time.time()
        logger.debug(f"Query {sql} took {end_time - start_time} seconds.")
        return cursor