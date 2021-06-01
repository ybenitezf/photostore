from whoosh.fields import BOOLEAN, DATETIME, ID, KEYWORD, SchemaClass
from whoosh.fields import TEXT
from whoosh.analysis import LanguageAnalyzer

class PhotoIndexSchema(SchemaClass):

    md5 = ID(stored=True, unique=True)
    archive_on = DATETIME(stored=True, sortable=True)
    taken_on = DATETIME(stored=True, sortable=True)
    taken_by = TEXT(analyzer=LanguageAnalyzer('es'))
    archived = BOOLEAN(stored=True)
    keywords = KEYWORD(lowercase=True, commas=True, scorable=True)
    credit_line = TEXT(analyzer=LanguageAnalyzer('es'))
    excerpt = TEXT(analyzer=LanguageAnalyzer('es'))
    headline = TEXT(analyzer=LanguageAnalyzer('es'))
