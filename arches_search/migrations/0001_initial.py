from django.db import migrations


class Migration(migrations.Migration):

    initial = True
    dependencies = [
        ("models", "11499_add_editlog_resourceinstance_idx"),
    ]

    forward_sql = """
        INSERT INTO public.plugins(
            pluginid, name, icon, component, componentname, config, slug, sortorder, helptemplate)
            VALUES ('e42889e8-f8a8-4347-add3-f50aae161775', 
            '{"en": "Advanced Search"}', 
            'fa fa-search', 
            'views/components/plugins/arches-search', 
            'arches-search', 
            '{"show": true, "description": {"en": null}, "i18n_properties": ["description"]}', 
            'arches-search', 
            1, 
            ''
        );
        INSERT INTO public.functions(
            functionid, 
            functiontype, 
            name, 
            description, 
            defaultconfig, 
            modulename, 
            classname, 
            component
        )
        VALUES (
            '992da554-d18f-4c4a-bfab-51d308ca981d', 
            'global', 
            'Update Search Indices', 
            'Registers a global function to manage database indices for searchable values.', 
            null, 
            'search_indexing.py', 
            'SearchIndexingFunction', 
            null 
        );
    """
    reverse_sql = """
        DELETE FROM public.plugins WHERE pluginid = 'e42889e8-f8a8-4347-add3-f50aae161775';
        DELETE FROM public.functions WHERE functionid = '992da554-d18f-4c4a-bfab-51d308ca981d';
    """

    operations = [
        migrations.RunSQL(forward_sql, reverse_sql),
    ]
