# from django.apps import AppConfig

# class DeliveryConfig(AppConfig):
#     name = 'delivery'

#     def ready(self):
#         import delivery.signals  # Ensure the signals are imported


from django.apps import AppConfig

class DeliveryConfig(AppConfig):
    name = 'delivery'

    def ready(self):
        # import and register the signals
        import delivery.signals