import re
from django_hosts import patterns, host

host_patterns = patterns(
    "",
    host(
        re.sub(r"_", r"-", r"arches_search"), "arches_search.urls", name="arches_search"
    ),
)
