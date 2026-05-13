from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('owner', 'Project Owner'),
        ('viewer', 'Viewer'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='viewer')

    def __str__(self):
        return self.username
    
    def is_admin(self):
        return self.role == 'admin'

    def is_project_owner(self):
        return self.role == 'owner'

    def is_viewer(self):
        return self.role == 'viewer'

