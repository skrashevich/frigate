import peewee as pw
from playhouse.migrate import *
from playhouse.sqlite_ext import *

def migrate(migrator, database, fake=False, **kwargs):
    # Add a new temporary column to store the data
    migrator.add_column("event", "sub_label_tmp", pw.CharField(max_length=100, null=True))

    # Copy the data from the original column to the temporary column
    migrator.execute_sql("UPDATE event SET sub_label_tmp = sub_label")

    # Drop the original column
    migrator.drop_column("event", "sub_label")

    # Rename the temporary column to the original column name
    migrator.rename_column("event", "sub_label_tmp", "sub_label")

def rollback(migrator, database, fake=False, **kwargs):
    # Revert the changes in reverse order
    migrator.add_column("event", "sub_label_tmp", pw.CharField(max_length=20, null=True))
    migrator.execute_sql("UPDATE event SET sub_label_tmp = sub_label")
    migrator.drop_column("event", "sub_label")
    migrator.rename_column("event", "sub_label_tmp", "sub_label")
