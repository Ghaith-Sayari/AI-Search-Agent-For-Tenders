# mappings/mapper.py

from mappings.config import MAPPINGS
from mappings.schemas import CanonicalOpportunity
from pipeline.hashing import generate_unique_key


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


def build_canonical_opportunity(record):
    """
    Takes a raw record, maps it, generates its unique_key,
    and validates it into a CanonicalOpportunity.

    Raises pydantic.ValidationError if the record is invalid
    (e.g. missing title) — caller should catch this and route to DLQ.
    """
    db_record = map_record(record)

    db_record["unique_key"] = generate_unique_key(
    title=db_record.get("title") or "",
    source=db_record.get("source") or "",
    external_id=db_record.get("external_id") or "",
)

    return CanonicalOpportunity(**db_record)