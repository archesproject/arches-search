from typing import Callable

from django.apps import apps
from django.utils.module_loading import import_string


def discover_extension_instances(
    app_config_attribute: str,
    base_class: type,
    key_func: Callable[[object], str],
) -> dict[str, object]:
    """Instantiate every class listed under app_config.<app_config_attribute>
    across all installed apps, keyed by key_func."""
    registry: dict[str, object] = {}

    for app_config in apps.get_app_configs():
        for class_path in getattr(app_config, app_config_attribute, []):
            extension_class = import_string(class_path)
            if not (
                isinstance(extension_class, type)
                and issubclass(extension_class, base_class)
            ):
                raise TypeError(
                    f"{class_path} (from {app_config.name}.{app_config_attribute}) "
                    f"is not a subclass of {base_class.__name__}"
                )
            instance = extension_class()
            registry[key_func(instance)] = instance

    return registry
