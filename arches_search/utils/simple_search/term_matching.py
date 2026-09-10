from django.contrib.postgres.search import SearchQuery
from django.db.models import Q

REFERENCE_DATATYPE = "reference"
CONTROLLED_TERM_TYPE = "controlled-term"


def build_term_match_filter(term_text, datatype=None):
    """
    Q object matching TermSearch rows whose value either full-text-matches
    term_text (stemmed, whole-lexeme) or contains it as a substring
    (backed by the existing gin_trgm_ops index on TermSearch.value).
    Pass datatype to additionally restrict matches to that TermSearch.datatype.
    """
    full_text_query = SearchQuery(term_text, search_type="plain", config="english")
    match_filter = Q(search_vector=full_text_query) | Q(value__icontains=term_text)
    if datatype is not None:
        match_filter &= Q(datatype=datatype)
    return match_filter


def datatype_for_term(term):
    """
    Maps a request term dict's `type` to the TermSearch.datatype its match
    should be restricted to, or None for an unrestricted (plain-text) match.
    """
    return REFERENCE_DATATYPE if term.get("type") == CONTROLLED_TERM_TYPE else None
