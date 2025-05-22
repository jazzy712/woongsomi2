from django.contrib import admin
from .models import DepositProduct, DepositOption

class DepositOptionInline(admin.TabularInline):
    model = DepositOption
    extra = 0

@admin.register(DepositProduct)
class DepositProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'bank', 'created_at')
    inlines = [DepositOptionInline]
