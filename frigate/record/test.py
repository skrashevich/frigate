import glob
import logging
import os

from multiprocessing.synchronize import Event as MpEvent
from pathlib import Path

from peewee import DatabaseError, DoesNotExist, chunked
from playhouse.sqliteq import SqliteQueueDatabase
from frigate.config import FrigateConfig, RetainModeEnum
from frigate.const import RECORD_DIR, SECONDS_IN_DAY
from frigate.models import Event, Recordings, RecordingsToDelete, Timeline
from frigate.record.util import remove_empty_directories
from frigate.storage import StorageS3

logger = logging.getLogger(__name__)


def sync_files() -> None:
    config_file = os.environ.get("CONFIG_FILE", "/config/config.yml")
    # Check if we can use .yaml instead of .yml
    config_file_yaml = config_file.replace(".yml", ".yaml")
    if os.path.isfile(config_file_yaml):
        config_file = config_file_yaml

    config = FrigateConfig.parse_file(config_file)

    print("Start sync files.")

    db = SqliteQueueDatabase(
        config.database.path,
        pragmas={
            "auto_vacuum": "FULL",  # Does not defragment database
            "cache_size": -512 * 1000,  # 512MB of cache
            "synchronous": "NORMAL",  # Safe when using WAL https://www.sqlite.org/pragma.html#pragma_synchronous
        },
        timeout=60,
    )
    models = [Event, Recordings, Timeline, RecordingsToDelete]
    db.bind(models)

    # get all recordings in the db
    recordings = Recordings.select(Recordings.id, Recordings.path)

    # get all recordings files on disk and put them in a set
    files_on_disk = set(glob.glob(f"{RECORD_DIR}/**/*.mp4", recursive=True))

    # Use pagination to process records in chunks
    page_size = 1000
    num_pages = (recordings.count() + page_size - 1) // page_size
    files_to_check = set()

    for page in range(num_pages):
        for recording in recordings.paginate(page, page_size):
            files_to_check.add(recording.path)

    # Find files on disk that do not have corresponding records in database
    files_without_records = files_on_disk - files_to_check

    if files_without_records:
        print(
            f"Found {len(files_without_records)} files without corresponding records in the database"
        )

        for file_path in files_without_records:
            print(f"File without record: {file_path}")

        total_size_in_bytes = sum(os.path.getsize(f) for f in files_without_records)
        total_size_in_gb = total_size_in_bytes / (1024 * 1024 * 1024)
        print(f"Total size of files without record: {total_size_in_gb:.2f} GB")

    else:
        print("No files without corresponding records found.")

    print("End sync files.")


sync_files()
