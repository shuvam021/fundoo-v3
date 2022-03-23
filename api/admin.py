from django.contrib import admin
from api.models import User, Note, Label


# Register your models here.
admin.site.register(User)
admin.site.register(Note)
admin.site.register(Label)
