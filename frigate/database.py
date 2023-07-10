import logging
import time
import traceback

from peewee import SENTINEL
from playhouse.sqliteq import SqliteQueueDatabase

logger = logging.getLogger(__name__)


class TimedSqliteQueueDatabase(SqliteQueueDatabase):
    def execute_sql(self, sql, params=None, commit=SENTINEL, timeout=None):
        start_time = time.time()
        cursor = super().execute_sql(sql, params, commit, timeout)
        duration = time.time() - start_time
        self.log_query(sql, params, duration)
        return cursor

    @staticmethod
    def log_query(sql, params, duration):
        if duration < 0.1:
            logger.debug(
                "Query %s with params %s took %.2f seconds.",
                sql,
                params,
                duration,
            )
        else:
            call_stack = traceback.format_stack()
            logger.warning(
                "Query %s with params %s took %.2f seconds.\nCall stack: %s",
                sql,
                params,
                duration,
                "\n".join(call_stack),
            )
