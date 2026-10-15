from django.urls import path

from . import views, views_results

urlpatterns = [
    path("", views.index, name="index"),
    path("process/", views.stub, name="process"),
    path("evaluation/", views.stub, name="evaluation"),
    path("settings/", views.settings_page, name="settings"),
    path("settings/ollama-check/", views.ollama_check, name="ollama_check"),
    path("dictionaries/", views.dictionaries_page, name="dictionaries"),
    path("dictionaries/save/", views.dictionaries_save, name="dictionaries_save"),
    path("eda/", views.eda_page, name="eda"),
    path("eda/by-category/", views.eda_by_category, name="eda_by_category"),
    path("review/", views_results.results_page, name="review"),
    path("review/<int:pk>/", views_results.result_update, name="result_update"),
]