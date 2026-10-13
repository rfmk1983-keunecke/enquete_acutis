import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
class Command(BaseCommand):
    help='Cria administrador inicial se ADMIN_USERNAME e ADMIN_PASSWORD estiverem configurados.'
    def handle(self,*args,**kwargs):
        username=os.getenv('ADMIN_USERNAME');password=os.getenv('ADMIN_PASSWORD');email=os.getenv('ADMIN_EMAIL','')
        if not username or not password:return
        User=get_user_model()
        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(username=username,email=email,password=password)
            self.stdout.write('Administrador inicial criado.')
