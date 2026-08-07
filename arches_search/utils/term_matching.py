from django.contrib.postgres.search import SearchQuery
from django.db.models import Q


def build_term_match_filter(term_text):
    """
    Q object matching TermSearch rows whose value either full-text-matches
    term_text (stemmed, whole-lexeme) or contains it as a substring
    (backed by the existing gin_trgm_ops index on TermSearch.value).
    """
    full_text_query = SearchQuery(term_text, search_type="plain", config="english")
    return Q(search_vector=full_text_query) | Q(value__icontains=term_text)
