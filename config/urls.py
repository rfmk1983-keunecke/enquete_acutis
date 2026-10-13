from django.contrib import admin
from django.urls import path
from votacao import views, panel
admin.site.site_header='Eleição Escolar | Administração'
admin.site.site_title='Eleição Escolar'
admin.site.index_title='Gestão da eleição'
urlpatterns=[path('gestao/entrar/',panel.sign_in,name='manage_login'),path('gestao/sair/',panel.sign_out,name='manage_logout'),path('gestao/',panel.dashboard,name='manage_dashboard'),path('gestao/eleicao/',panel.edit_election,name='manage_election'),path('gestao/candidato/novo/',panel.candidate_form,name='manage_candidate_new'),path('gestao/candidato/<int:pk>/editar/',panel.candidate_form,name='manage_candidate_edit'),path('gestao/candidato/<int:pk>/excluir/',panel.delete_candidate,name='manage_candidate_delete'),path('gestao/eleicao/<str:action>/',panel.change_status,name='manage_status'),path('',views.home,name='home'),path('votar/',views.vote,name='vote'),path('confirmacao/',views.success,name='success'),path('foto/<int:pk>/',views.photo,name='photo'),path('painel/resultado/',views.results,name='results'),path('painel/auditoria.csv',views.export_csv,name='export_csv'),path('admin/',admin.site.urls)]
