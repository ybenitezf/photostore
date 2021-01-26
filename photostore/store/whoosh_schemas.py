from whoosh.fields import BOOLEAN, DATETIME, ID, KEYWORD, SchemaClass
from whoosh.fields import TEXT

class PhotoIndexSchema(SchemaClass):

    md5 = ID(stored=True, unique=True)
    archive_on = DATETIME(stored=True, sortable=True)
    taken_on = DATETIME(stored=True, sortable=True)
    taken_by = TEXT
    archived = BOOLEAN(stored=True)
    keywords = KEYWORD(lowercase=True, commas=True, scorable=True)
    credit_line = TEXT
    excerpt = TEXT
    headline = TEXT
