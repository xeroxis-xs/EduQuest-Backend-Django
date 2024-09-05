from django.test.runner import DiscoverRunner
from django.core.management import call_command

class PopulateDBBeforeTest(DiscoverRunner):
    def setup_databases(self, **kwargs):
        result = super().setup_databases(**kwargs)
        # Replace 'your_custom_command' with the actual name of your management command
        call_command('populate_prod_db')
        return result