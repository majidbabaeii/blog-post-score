from django.utils import timezone
from rest_framework import serializers

from blog.models import Post, Score


class PostSerializer(serializers.HyperlinkedModelSerializer):
    user_score = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ["id", "url", "title", "description", "score", "user_score"]

    def get_user_score(self, post):
        """
        Retrieve the score given by the current authenticated user to the given post.
        Returns:
            int or None: The score given by the current user, or None if the user is not authenticated or has not scored the post.
        """

        score = None
        if (
            self.context.get("request")
            and self.context["request"].user.is_authenticated
        ):
            user_score_obj = Score.get_user_score(
                post=post, user=self.context["request"].user, raise_exception=False
            )
            score = user_score_obj and user_score_obj.score

        return score


class ScoreSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault(),
    )

    class Meta:
        model = Score
        fields = ["score", "created_at", "user"]
        read_only_fields = ["post", "updated_at"]
