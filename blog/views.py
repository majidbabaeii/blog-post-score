from django.shortcuts import render
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from blog.models import Post, Score
from blog.serializer import PostSerializer, ScoreSerializer


class PostViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]
    queryset = Post.objects.all()
    serializer_class = PostSerializer

    @action(detail=True, serializer_class=ScoreSerializer, methods=["POST"])
    def score(self, request, pk: int):
        post_obj = self.get_object()
        user_score_obj = Score.get_user_score(
            post=post_obj, user=request.user, raise_exception=False
        )
        serializer = ScoreSerializer(
            data=request.data,
            context=self.get_serializer_context(),
            instance=user_score_obj,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(post=post_obj)

        return Response(serializer.data, status=status.HTTP_201_CREATED)
