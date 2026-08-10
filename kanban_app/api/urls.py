"""URL routes exposed by the kanban app."""

from django.urls import path

from .views import BoardListCreateView

urlpatterns = [
    path('boards/', BoardListCreateView.as_view(), name='board-list'),
]
