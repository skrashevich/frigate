"""Run recording maintainer and cleanup."""

import logging
import multiprocessing as mp
import signal
import threading

from setproctitle import setproctitle
from types import FrameType
from typing import Optional

from playhouse.sqliteq import SqliteQueueDatabase

from frigate.config import FrigateConfig
from frigate.models import Event, Recordings, RecordingsToDelete, Timeline
from frigate.record.cleanup import RecordingCleanup
from frigate.record.maintainer import RecordingMaintainer
from frigate.types import RecordMetricsTypes
from frigate.util import listen
from frigate.database import TimedSqliteQueueDatabase

logger = logging.getLogger(__name__)


def manage_recordings(
    config: FrigateConfig,
    recordings_info_queue: mp.Queue,
    process_info: dict[str, RecordMetricsTypes],
) -> None:
    stop_event = mp.Event()

    def receiveSignal(signalNumber: int, frame: Optional[FrameType]) -> None:
        stop_event.set()

    signal.signal(signal.SIGTERM, receiveSignal)
    signal.signal(signal.SIGINT, receiveSignal)

    threading.current_thread().name = "process:recording_manager"
    setproctitle("frigate.recording_manager")
    listen()

    db = TimedSqliteQueueDatabase(config.database.path)
    models = [Event, Recordings, Timeline, RecordingsToDelete]
    db.bind(models)

    maintainer = RecordingMaintainer(
        config, recordings_info_queue, process_info, stop_event
    )
    maintainer.start()

    cleanup = RecordingCleanup(config, stop_event)
    cleanup.start()

    logger.info("recording_manager: exiting subprocess")
