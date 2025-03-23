from django.apps import AppConfig


class InvestBotConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.invest_bot'
    verbose_name = 'Telegram Bot'

    def ready(self):
        # Import handlers when app is ready
        from . import handlers
