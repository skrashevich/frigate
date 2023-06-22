from playhouse.sqliteq import SqliteQueueDatabase
from peewee import SENTINEL
import time

import loggin

logger = logging.getLogger(__name__)


class TimedSqliteQueueDatabase(SqliteQueueDatabase):
    def execute_sql(self, sql, params=None, commit=SENTINEL, timeout=None):
        start_time = time.time()
        cursor = super().execute_sql(sql, params, commit, timeout)
        end_time = time.time()
        duration = end_time - start_time
        logger.debug(f"Query {sql} with params {params} took {duration:.2f} seconds.")
        span.set_attribute("sql.query", sql)
        span.set_attribute("sql.params", str(params))
        span.set_attribute("sql.duration", duration)
        return cursor
