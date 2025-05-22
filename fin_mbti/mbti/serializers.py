from rest_framework import serializers
from .models import (
    Survey, SurveyQuestion, SurveyResponse, 
    PersonalityType, Character, FinancialProduct, 
    Recommendation, UserShare
)

class SurveySerializer(serializers.ModelSerializer):
    class Meta:
        model = Survey
        fields = '__all__'

class SurveyQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SurveyQuestion
        fields = '__all__'

class SurveyResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = SurveyResponse
        fields = '__all__'

class CharacterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Character
        fields = '__all__'

class PersonalityTypeSerializer(serializers.ModelSerializer):
    character = CharacterSerializer(read_only=True)
    
    class Meta:
        model = PersonalityType
        fields = '__all__'

class FinancialProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinancialProduct
        fields = '__all__'

class RecommendationSerializer(serializers.ModelSerializer):
    product = FinancialProductSerializer(read_only=True)
    personality_type = PersonalityTypeSerializer(read_only=True)
    
    class Meta:
        model = Recommendation
        fields = '__all__'

class UserShareSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserShare
        fields = '__all__'
