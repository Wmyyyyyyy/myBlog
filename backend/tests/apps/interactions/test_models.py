import pytest
from apps.interactions.models import Favorite, Like, Follow


class TestFavoriteModel:
    def test_favorite_create(self):
        fav = Favorite(user_id="user-1", blog_id="blog-1")
        assert fav.user_id == "user-1"
        assert fav.blog_id == "blog-1"


class TestLikeModel:
    def test_like_create(self):
        like = Like(user_id="user-1", blog_id="blog-1")
        assert like.user_id == "user-1"
        assert like.blog_id == "blog-1"


class TestFollowModel:
    def test_follow_create(self):
        follow = Follow(follower_id="user-1", following_id="user-2")
        assert follow.follower_id == "user-1"
        assert follow.following_id == "user-2"