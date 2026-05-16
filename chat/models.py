from django.db import models

class Conversation(models.Model):
    phone_e164 = models.CharField(max_length=20, unique=True)
    session_json = models.JSONField(default=dict)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Chat: {self.phone_e164}"
