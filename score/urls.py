from django.urls import path, include
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("dao", views.dao, name="dao"),
    path("set_chart", views.set_chart, name="set_chart"),
    path("proposal_info", views.proposl_info, name="proposal_info"),
]
