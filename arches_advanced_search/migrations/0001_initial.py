from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("afrc", "0001_initial"),
    ]

    forward_sql = """
        INSERT INTO public.plugins(
            pluginid, name, icon, component, componentname, config, slug, sortorder, helptemplate)
            VALUES ('e42889e8-f8a8-4347-add3-f50aae161775', 
            '{"en": "Advanced Search"}', 
            'fa fa-search', 
            'views/components/plugins/arches-advanced-search', 
            'arches-advanced-search', 
            '{"show": true, "description": {"en": null}, "i18n_properties": ["description"]}', 
            'arches-advanced-search', 
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
