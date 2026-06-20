from django.apps import AppConfig


class InventoryConfig(AppConfig):
    name = 'inventory'

    def ready(self):
        # On app (process) startup, generate a new server start id
        # so that sessions from previous process instances are invalidated.
        try:
            from django.core.cache import cache
            import uuid
            cache.set('SITE_SERVER_START_ID', uuid.uuid4().hex, None)
        except Exception:
            # Avoid import-time failures during migrations or management commands
            pass

        # Ensure signal handlers are connected
        try:
            from . import signals  # noqa: F401
        except Exception:
            pass
