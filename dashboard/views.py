from django.db.models import Count, Q
from django.utils.dateparse import parse_date
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from coding.models import Submission


class PieChartDataView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        date = request.GET.get('date')

        stats = []
        if date:
            parsed_date = parse_date(date)
            if not parsed_date:
                return Response({'error': 'Invalid date format'}, status=400)

            stats = Submission.objects.filter(
                user=user,
                created_at__date=parsed_date
            ).values('created_at__date').annotate(
                correct_count=Count('id', filter=Q(is_correct=True)),
                incorrect_count=Count('id', filter=Q(is_correct=False))
            )
        else:
            latest_submission = Submission.objects.filter(user=user)
            if latest_submission.exists():
                latest_submission = latest_submission.latest('updated_at')
                stats = Submission.objects.filter(
                    user=user,
                    created_at__date=latest_submission.created_at.date()
                ).values('created_at__date').annotate(
                    correct_count=Count('id', filter=Q(is_correct=True)),
                    incorrect_count=Count('id', filter=Q(is_correct=False))
                )

        return Response({'pie_chart_stats': list(stats),
                         'get_progress_over_time': get_progress_over_time(request)})


def get_progress_over_time(request):
    # Ensure the user is authenticated
    if not request.user.is_authenticated:
        raise ("User not authenticated")

    user = request.user

    # Fetch progress data for the authenticated user
    progress = Submission.objects.filter(user=user).values('created_at__date').annotate(
        correct_count=Count('id', filter=Q(is_correct=True)),
        incorrect_count=Count('id', filter=Q(is_correct=False))
    ).order_by('created_at__date')

    return {'progress': list(progress)}
