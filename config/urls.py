from django.contrib import admin
from django.urls import path
from votacao import views
admin.site.site_header='Eleição Escolar | Administração'
admin.site.site_title='Eleição Escolar'
admin.site.index_title='Gestão da eleição'
urlpatterns=[path('',views.home,name='home'),path('votar/',views.vote,name='vote'),path('confirmacao/',views.success,name='success'),path('foto/<int:pk>/',views.photo,name='photo'),path('painel/resultado/',views.results,name='results'),path('painel/auditoria.csv',views.export_csv,name='export_csv'),path('admin/',admin.site.urls)]
