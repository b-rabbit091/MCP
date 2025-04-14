# 3. coding/serializers.py
from rest_framework import serializers

from .models import Case, Submission


class CaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Case
        exclude = ['icd10_id', 'created_at']


class SubmissionSerializer(serializers.ModelSerializer):
    submitted_icd = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=False
    )
    case_number = serializers.CharField(write_only=True)

    class Meta:
        model = Submission
        fields = ['case_number', 'submitted_icd']

    def to_internal_value(self, data):
        internal = super().to_internal_value(data)
        
        # Get the case number (which is actually the case id) from the validated data
        case_number = internal['case_number']
        
        try:
            # Convert the string case_number to integer and get the case object
            case_id = int(case_number)
            case = Case.objects.get(id=case_id)
            # Replace case_number with the actual case object
            internal['case'] = case
            del internal['case_number']  # Remove the case_number as it's not needed anymore
        except (ValueError, TypeError):
            raise serializers.ValidationError({"case_number": "Case number must be a valid integer."})
        except Case.DoesNotExist:
            raise serializers.ValidationError({"case_number": "Case with this id does not exist."})
        
        return internal

    def create(self, validated_data):
        # The validated_data now contains the case object instead of case_number
        return Submission.objects.create(**validated_data)
