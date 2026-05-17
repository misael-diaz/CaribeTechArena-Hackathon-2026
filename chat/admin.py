from django.contrib import admin
from .models import Conversation

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('phone_e164', 'updated_at')
    search_fields = ('phone_e164',)
    readonly_fields = ('updated_at',)
