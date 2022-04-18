import logging

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import post_save

from api.tasks import task_send_verify_user_email

logger = logging.getLevelName(__name__)


# Create your models here.
class User(AbstractUser):
    """Extend class Default User model with custom fields"""
    email = models.EmailField(unique=True, max_length=255)
    password = models.CharField(max_length=255)
    is_verified = models.BooleanField(default=False)
    username = models.CharField(max_length=255, blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'password',)

    class Meta:
        db_table = 'user'
        verbose_name = 'user'
        verbose_name_plural = 'users'


def user_post_save(sender, instance, created, *args, **kwargs):
    if created:
        try:
            task_send_verify_user_email.delay(instance.id, instance.email)
        except Exception as e:
            logger.exception(e)


post_save.connect(user_post_save, sender=User)


class Note(models.Model):
    """ORM for all Notes"""
    title = models.CharField(max_length=255)
    description = models.TextField()
    user = models.ForeignKey('api.User', on_delete=models.CASCADE)
    color = models.CharField(max_length=255, null=True, blank=True)
    is_archived = models.BooleanField(default=False)

    class Meta:
        db_table = 'note'
        verbose_name = 'note'
        verbose_name_plural = 'notes'
        ordering = ['pk']


class Label(models.Model):
    """ORM for Label table"""
    title = models.CharField(max_length=255)
    color = models.CharField(max_length=50)
    author = models.ForeignKey('api.User', on_delete=models.CASCADE)
    is_archived = models.BooleanField(default=False)
    # note = models.ManyToManyField('api.Note')

    class Meta:
        db_table = 'label'
        verbose_name = 'label'
        verbose_name_plural = 'labels'
