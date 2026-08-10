"""URL routes exposed by the kanban app."""

from django.urls import path

from .views import (AssignedTaskListView, BoardDetailView,
                    BoardListCreateView, ReviewingTaskListView,
                    TaskCreateView, TaskDetailView)

urlpatterns = [
    path('boards/', BoardListCreateView.as_view(), name='board-list'),
    path('boards/<int:pk>/', BoardDetailView.as_view(), name='board-detail'),
    path('tasks/', TaskCreateView.as_view(), name='task-create'),
    path('tasks/assigned-to-me/', AssignedTaskListView.as_view(),
         name='task-assigned-to-me'),
    path('tasks/reviewing/', ReviewingTaskListView.as_view(),
         name='task-reviewing'),
    path('tasks/<int:pk>/', TaskDetailView.as_view(), name='task-detail'),
]
