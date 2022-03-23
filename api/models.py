from django.contrib.auth.models import AbstractUser
from django.db import models


# Create your models here.
class User(AbstractUser):
    """Extend class Default User model with custom fields"""
    email = models.EmailField(unique=True, max_length=255)
    password = models.CharField(max_length=255)
    is_verified = models.BooleanField(default=False)
    username = models.CharField(max_length=255, blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'password', )

    class Meta:
        db_table = 'user'
        verbose_name = 'user'
        verbose_name_plural = 'users'


class Note(models.Model):
    """ORM for all Notes"""
    title = models.CharField(max_length=255)
    description = models.TextField()
    user = models.ForeignKey('api.User', on_delete=models.CASCADE)

    class Meta:
        db_table = 'note'
        verbose_name = 'note'
        verbose_name_plural = 'notes'


class Label(models.Model):
    """ORM for Label table"""
    title = models.CharField(max_length=255)
    color = models.CharField(max_length=50)
    author = models.ForeignKey('api.User', on_delete=models.PROTECT)
    note = models.ManyToManyField('api.Note')

    class Meta:
        db_table = 'label'
        verbose_name = 'label'
        verbose_name_plural = 'labels'
