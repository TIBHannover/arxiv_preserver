from django.contrib import admin
from . import models

# Register your models here.

admin.site.register(models.Paper)
admin.site.register(models.Category)
admin.site.register(models.PaperUserRelation)
admin.site.register(models.PaperUserTag)
admin.site.register(models.Tweet)
admin.site.register(models.TweetArxiv)
