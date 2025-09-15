import re
from django_hosts import patterns, host

host_patterns = patterns(
    "",
    host(re.sub(r"_", r"-", r"arches_advanced_search"), "arches_advanced_search.urls", name="arches_advanced_search"),
)
