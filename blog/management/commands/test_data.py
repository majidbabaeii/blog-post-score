from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.core.management import BaseCommand


class Command(BaseCommand):
    help = "add Some Test Data to work with"

    def handle(self, *args, **options):
        User.objects.bulk_create(
            [
                User(
                    username=f"user{i}",
                    password=make_password("1234"),
                    is_active=True,
                )
                for i in range(10)
            ],
            ignore_conflicts=True,
        )

        admin_user = User.objects.filter(username="admin").first()
        if not admin_user:
            User.objects.create_superuser("admin", "admin@example.com", "1234")
