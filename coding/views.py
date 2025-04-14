from django.db.models import Subquery
from django.utils import timezone
from rest_framework import generics
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from coding.models import Submission, ICD10
from coding.serializers import SubmissionSerializer
from .models import Case
from .serializers import CaseSerializer


class CaseListView(generics.ListAPIView):
    serializer_class = CaseSerializer

    def get_queryset(self):
        user = self.request.user

        # Get a single incorrect submission (random)
        submission = Submission.objects.filter(
            user=user.id,
            is_correct__in=[False, None]
        ).order_by('?').values('case_number')[:1]
        # Try to return the corresponding case

        case = Case.objects.filter(id__in=Subquery(submission)).first()

        # If no incorrect submission exists, return a completely random case
        if not case:
            case = Case.objects.order_by('?')[:1]

        return case


class SubmissionViewSet(viewsets.ModelViewSet):
    queryset = Submission.objects.all()
    serializer_class = SubmissionSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        # Use the default serializer to validate the data
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Extract validated data
        case = serializer.validated_data['case']
        submitted_icd = serializer.validated_data['submitted_icd']

        # Fetch ICD objects for validation
        icd_objects = ICD10.objects.filter(code__in=submitted_icd)
        valid_icd_codes = set(icd_objects.values_list('code', flat=True))

        # Create Submission instances and check validity of each ICD code
        submissions = [
            Submission(
                user=request.user,
                case_number=case,
                submitted_icd=icd_code,
                is_correct=icd_code in valid_icd_codes,
                created_at=timezone.now()
            )
            for icd_code in submitted_icd
        ]

        # Bulk create the submissions
        Submission.objects.bulk_create(submissions)

        # Return a response with a success message
        return Response({"next": True}, status=status.HTTP_200_OK)