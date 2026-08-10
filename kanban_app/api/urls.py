"""URL routes exposed by the kanban app."""

from django.urls import path

from .views import BoardDetailView, BoardListCreateView

urlpatterns = [
    path('boards/', BoardListCreateView.as_view(), name='board-list'),
    path('boards/<int:pk>/', BoardDetailView.as_view(), name='board-detail'),
]
