from django.db import models
from django.contrib.auth.models import User

class SearchHistoryModel(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    city = models.CharField(max_length=50)
    searched_at = models.DateTimeField(auto_now_add=True)
