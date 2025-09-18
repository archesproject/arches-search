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
    """
    reverse_sql = """
        DELETE FROM public.plugins WHERE pluginid = 'e42889e8-f8a8-4347-add3-f50aae161775';
    """

    operations = [
        migrations.RunSQL(forward_sql, reverse_sql),
    ]
