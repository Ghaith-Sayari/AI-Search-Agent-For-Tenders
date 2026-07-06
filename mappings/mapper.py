# mappings/mapper.py

from mappings.config import MAPPINGS


def map_record(record):

    source = record["source"]
    config = MAPPINGS[source]

    db_record = {
        "source": source
    }

    for db_field, source_field in config.items():

        if source_field is None:
            db_record[db_field] = None
        else:
            db_record[db_field] = record.get(source_field)

    return db_record