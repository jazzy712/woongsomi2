from django.contrib import admin
from .models import *

class QuestionInline(admin.TabularInline):
    model = SurveyQuestion
    extra = 1

@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    inlines = [QuestionInline]
    list_display = ('title', 'created_at')
    
@admin.register(PersonalityType)
class TypeAdmin(admin.ModelAdmin):
    list_display = ('type_code', 'name', 'risk_preference', 'consumption_style', 'goal_orientation')
    search_fields = ('type_code',)

@admin.register(FinancialProduct)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'provider', 'product_type', 'risk_level')
    list_filter = ('product_type', 'risk_level')
