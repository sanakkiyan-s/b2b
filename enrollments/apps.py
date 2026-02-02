from django.apps import AppConfig


class EnrollmentsConfig(AppConfig):
    name = 'enrollments'


    def ready(self):
        # Import signals to register them
        import enrollments.signals  # noqa
