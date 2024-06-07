from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Sum
from django.utils import timezone

from blog.utils import calculate_score, calculate_slope


class Post(models.Model):
    """
    A model representing a post with a title and description, including
    methods to calculate and retrieve its score based on various parameters.
    """

    title = models.CharField(max_length=255, default="{1+1}")
    description = models.TextField()

    def get_today_score_data(self):
        """
        Retrieve the score data for the current day from the CalculatedScore model.

        Returns:
            dict: A dictionary containing 'total_score' and 'num_users_scored' for the current day.
                  If no data is found for today, returns {'total_score': 0, 'num_users_scored': 0}.
        """
        today_date = timezone.now().date()
        today_score_data = CalculatedScore.objects.filter(
            post=self, date=today_date
        ).values("total_score", "num_users_scored")

        if today_score_data:
            score_data = today_score_data[0]
        else:
            score_data = {
                "total_score": 0,
                "num_users_scored": 0,
            }
        return score_data

    def calculate_post_score(self):
        """
        Calculate the score of the post, considering both historical and today's score data.

        Returns:
            float: The final calculated score of the post.
        """
        today_date = timezone.now().date()

        score_data = (
            CalculatedScore.objects.filter(post=self)
            .exclude(date=today_date)
            .aggregate(
                total_score=Sum("total_score", default=0),
                num_users_scored=Sum("num_users_scored", default=0),
            )
        )

        today_score_data = self.get_today_score_data()

        score = calculate_score(**score_data)
        today_score = calculate_score(**today_score_data)

        slope = calculate_slope(today_score, score)

        if slope >= -abs(settings.SLOPE_THRESHOLD):
            final_score = calculate_score(
                total_score=score_data["total_score"] + today_score_data["total_score"],
                num_users_scored=score_data["num_users_scored"]
                + today_score_data["num_users_scored"],
            )
        else:
            final_score = score
        return final_score

    @property
    def score(self):
        """
        Retrieve the cached score of the post. If not cached, calculate the score
        and cache it for future retrieval.

        Returns:
            float: The cached or calculated score of the post.
        """
        score = cache.get(f"post_{self.id}_score")
        if score is None:
            score = self.calculate_post_score()
            cache.set(f"post_{self.id}_score", score, 10)
        return score


class CalculatedScore(models.Model):
    """
    A model representing the calculated score data for a post on a specific date.
    Includes fields for storing the score, total score, number of users scored,
    and a flag indicating if an update is needed.
    """

    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    date = models.DateField(null=False, db_index=True)

    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    score = models.FloatField(
        validators=[MaxValueValidator(5), MinValueValidator(0)], default=0
    )
    total_score = models.PositiveIntegerField(default=0)
    num_users_scored = models.PositiveIntegerField(default=0)
    need_update = models.BooleanField(default=True, db_index=True)

    class Meta:
        unique_together = ["post", "date"]
        index_together = [
            ["post", "date", "need_update"],
        ]

    @staticmethod
    def get_calculated_score_object(score: "Score"):
        """
        Retrieve or create a CalculatedScore object for a given score's post and date.
        Returns:
            CalculatedScore: The retrieved or newly created CalculatedScore object.
        """
        date_time = score.created_at or timezone.now()
        date = date_time.date()
        return CalculatedScore.objects.get_or_create(post=score.post, date=date)[0]


class Score(models.Model):
    """
    A model representing the score given by a user to a post.
    """

    # in real Application we need to set auto_now_add=True,
    # but now for test Purpose,I disable this option to let the tester set the creation time
    created_at = models.DateTimeField(
        auto_now_add=False, db_index=True, default=timezone.now
    )
    updated_at = models.DateTimeField(auto_now=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    score = models.PositiveIntegerField(
        validators=[MaxValueValidator(5), MinValueValidator(0)]
    )
    calculated_score = models.ForeignKey(
        CalculatedScore, on_delete=models.CASCADE, related_name="score_objects"
    )

    @staticmethod
    def get_user_score(post: Post, user: User, raise_exception=True) -> "Score":
        """
        Retrieve the score given by a specific user to a specific post.

        Returns:
            Score: The retrieved score object, or None if not found and raise_exception is False.

        Raises:
            Score.DoesNotExist: If no score is found and raise_exception is True.
        """
        try:
            user_score = Score.objects.get(post=post, user=user)
        except Score.DoesNotExist as e:
            if raise_exception:
                raise e
            user_score = None
        return user_score

    def save(self, *args, **kwargs):
        """
        Save the Score object, ensuring the related CalculatedScore object is set and updated if needed.
        """
        if not self.calculated_score_id:
            self.calculated_score = CalculatedScore.get_calculated_score_object(self)

        if not self.calculated_score.need_update:
            self.calculated_score.need_update = True
            self.calculated_score.save()

        super().save(*args, **kwargs)

    class Meta:
        unique_together = ["post", "user"]
        index_together = [
            ["post", "user"],
        ]
