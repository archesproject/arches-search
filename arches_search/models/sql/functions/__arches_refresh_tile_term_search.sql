CREATE OR REPLACE FUNCTION _arches_search_update_term_values(_tileid UUID)
RETURNS VOID AS $$
BEGIN
    DELETE FROM afrc_searchable_values WHERE afrc_searchable_values.tileid = _tileid;
    INSERT INTO afrc_searchable_values (tileid, resourceinstanceid, value)
    SELECT DISTINCT
        t.tileid,
        t.resourceinstanceid,
        CASE 
            WHEN n.datatype = 'non-localized-string' THEN data.value::jsonb->'value'
            WHEN n.datatype = 'string' THEN data.value::jsonb->'en'->>'value'
            WHEN n.datatype = 'concept' THEN __arches_get_concept_label(data.value::uuid)
            WHEN n.datatype = 'concept-list' THEN __arches_get_concept_list_label(data.value::jsonb, 'en')
        END AS value
    FROM 
        tiles t
    CROSS JOIN LATERAL jsonb_each_text(t.tiledata) AS data(nodeid, value) 
    JOIN 
        nodes n ON data.nodeid::uuid = n.nodeid
    WHERE 
        n.datatype IN ('string', 'concept', 'concept-list')
        AND (
            (n.datatype = 'string' AND data.value::jsonb->'en'->>'value' IS NOT NULL) OR
            (n.datatype IN ('concept', 'concept-list') AND data.value IS NOT NULL)
        )
        AND t.tileid = _tileid;
    UPDATE public.afrc_searchable_values
        SET search_vector = setweight(to_tsvector('english', coalesce(value,'')), 'A'); 
END; 

$$ LANGUAGE plpgsql;