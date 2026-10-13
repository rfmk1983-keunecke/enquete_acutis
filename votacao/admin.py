from django.contrib import admin,messages
from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from PIL import Image
from io import BytesIO
from .models import Election,Candidate,Vote

@admin.register(Election)
class ElectionAdmin(admin.ModelAdmin):
    list_display=('title','status','started_at','ended_at')
    readonly_fields=('status','started_at','ended_at','created_at')
    actions=['start_election','close_election']
    def has_add_permission(self,request):return super().has_add_permission(request) and not Election.objects.exists()
    def has_delete_permission(self,request,obj=None):return bool(obj and obj.status==Election.DRAFT and not obj.candidates.exists())
    @admin.action(description='INICIAR eleição selecionada (bloqueia candidatos)')
    def start_election(self,request,queryset):
        for obj in queryset:
            with transaction.atomic():
                e=Election.objects.select_for_update().get(pk=obj.pk)
                if e.status!=Election.DRAFT or not e.candidates.exists():self.message_user(request,'A eleição precisa estar em preparação e ter candidatos.',messages.ERROR);continue
                e.status=Election.OPEN;e.started_at=timezone.now();e.save()
                self.message_user(request,'Eleição iniciada. Cadastro bloqueado.',messages.SUCCESS)
    @admin.action(description='ENCERRAR eleição selecionada (irreversível)')
    def close_election(self,request,queryset):
        for obj in queryset:
            with transaction.atomic():
                e=Election.objects.select_for_update().get(pk=obj.pk)
                if e.status!=Election.OPEN:self.message_user(request,'Apenas eleições em andamento podem ser encerradas.',messages.ERROR);continue
                e.status=Election.CLOSED;e.ended_at=timezone.now();e.save()
                self.message_user(request,'Eleição encerrada.',messages.SUCCESS)

class CandidateForm(forms.ModelForm):
    upload_photo=forms.ImageField(label='Foto do candidato (até 1 MB)',required=False)
    class Meta:
        model=Candidate
        fields=('election','name','email','number')
    def clean_upload_photo(self):
        photo=self.cleaned_data.get('upload_photo')
        if photo and photo.size>1024*1024:raise ValidationError('A foto deve ter até 1 MB.')
        return photo

@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    form=CandidateForm
    list_display=('number','name','email','election')
    search_fields=('name','email')
    def get_readonly_fields(self,request,obj=None):
        if obj and obj.election.status!=Election.DRAFT:return ('election','name','email','number')
        return ()
    def has_add_permission(self,request):return super().has_add_permission(request) and Election.objects.filter(status=Election.DRAFT).exists()
    def has_change_permission(self,request,obj=None):
        return super().has_change_permission(request,obj) and (obj is None or obj.election.status==Election.DRAFT)
    def has_delete_permission(self,request,obj=None):
        if obj:return super().has_delete_permission(request,obj) and obj.election.status==Election.DRAFT
        return super().has_delete_permission(request) and Election.objects.filter(status=Election.DRAFT).exists()
    def save_model(self,request,obj,form,change):
        upload=form.cleaned_data.get('upload_photo')
        if upload:
            im=Image.open(upload)
            im.thumbnail((600,600))
            im=im.convert('RGB')
            out=BytesIO();im.save(out,format='JPEG',quality=82)
            obj.photo_data=out.getvalue();obj.photo_type='image/jpeg'
        obj.save()
    def delete_queryset(self,request,queryset):
        for obj in queryset:obj.delete()

@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display=('id','election','voter_name','voter_email','candidate','created_at','ip_address')
    list_filter=('election','candidate','created_at')
    search_fields=('voter_name','voter_email')
    readonly_fields=('election','candidate','voter_name','voter_email','ip_address','user_agent','created_at')
    def has_add_permission(self,request):return False
    def has_change_permission(self,request,obj=None):return super().has_view_permission(request,obj)
    def has_delete_permission(self,request,obj=None):return False
    def delete_queryset(self,request,queryset):raise ValidationError('Votos não podem ser excluídos.')
