from celery import shared_task
from django.db.models import Count, F, OuterRef, Subquery, Sum

from blog.models import CalculatedScore, Score
from blog.utils import calculate_score


@shared_task(name="run_all_score_calculation")
def run_all_score_calculation_task(*args, **kwargs):
    """
    Celery task to enqueue score calculation tasks for all CalculatedScore objects
    that need to be updated.
    """

    for item in CalculatedScore.objects.filter(need_update=True).iterator():
        calculate_score_task.delay(item.pk)


@shared_task(name="calculate_score")
def calculate_score_task(pk, *args, **kwargs):
    """
    Celery task to calculate and update the score for a given CalculatedScore object.
    """
    calculated_score_obj: CalculatedScore = (
        CalculatedScore.objects.filter(pk=pk)
        .annotate(
            score_sum=Sum("score_objects__score", default=0),
            score_count=Count("score_objects"),
        )
        .first()
    )
    calculated_score_obj.total_score = calculated_score_obj.score_sum
    calculated_score_obj.num_users_scored = calculated_score_obj.score_count
    calculated_score_obj.score = calculate_score(
        total_score=calculated_score_obj.score_sum,
        num_users_scored=calculated_score_obj.score_count,
    )
    calculated_score_obj.need_update = False
    calculated_score_obj.save()


@shared_task(name="calculate_all_score")
def calculate_all_score_task(*args, **kwargs):
    """
    Celery task to calculate and update the scores for all CalculatedScore objects that need an update.
    This approach uses a single query to the database to update all relevant fields.

    Note:
        This method is currently not optimized and should be benchmarked and tested thoroughly
        before being used in a production environment.
    """
    subquery = CalculatedScore.objects.filter(id=OuterRef("id")).annotate(
        score_sum=Sum("score_objects__score"),
        score_count=Count("score_objects"),
        average_score=F("score_sum") / F("score_count"),
    )
    CalculatedScore.objects.filter(need_update=True).update(
        num_users_scored=Subquery(
            subquery.values(
                "score_count",
            )
        ),
        total_score=Subquery(
            subquery.values(
                "score_sum",
            )
        ),
        score=Subquery(
            subquery.values(
                "average_score",
            )
        ),
        need_update=False,
    )
