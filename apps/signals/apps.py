from django.apps import AppConfig


class SignalsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.signals'
    verbose_name = 'Signallar'

    def ready(self):
        # Signal handlerlarni import qilish
        pass
