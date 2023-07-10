import logging
import time

from peewee import SENTINEL
from playhouse.sqliteq import SqliteQueueDatabase

logger = logging.getLogger(__name__)


class TimedSqliteQueueDatabase(SqliteQueueDatabase):
    def execute_sql(self, sql, params=None, commit=SENTINEL, timeout=None):
        start_time = time.time()
        cursor = super().execute_sql(sql, params, commit, timeout)
        duration = time.time() - start_time
        logger.debug(f"Query {sql} with params {params} took {duration:.2f} seconds.")
        return cursor
