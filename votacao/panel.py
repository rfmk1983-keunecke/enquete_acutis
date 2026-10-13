from io import BytesIO
from PIL import Image, UnidentifiedImageError
from django import forms
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST
from .models import Election, Candidate, Vote


def is_admin(user):
    return user.is_active and user.is_staff

admin_required = user_passes_test(is_admin, login_url='/gestao/entrar/')

class ElectionForm(forms.ModelForm):
    class Meta:
        model = Election
        fields = ('title', 'description')
        widgets = {'title': forms.TextInput(attrs={'placeholder':'Ex.: Representantes da Turma 2026'}),
                   'description': forms.TextInput(attrs={'placeholder':'Uma frase sobre a eleição (opcional)'})}

class CandidateForm(forms.ModelForm):
    upload_photo = forms.ImageField(label='Foto do candidato', required=False, help_text='JPG ou PNG, até 1 MB')
    class Meta:
        model = Candidate
        fields = ('name','email','number')
        widgets = {'name': forms.TextInput(attrs={'placeholder':'Nome completo'}),
                   'email': forms.EmailInput(attrs={'placeholder':'nome@escola.com'}),
                   'number': forms.NumberInput(attrs={'min':'1','placeholder':'Ex.: 10'})}
    def clean_upload_photo(self):
        photo=self.cleaned_data.get('upload_photo')
        if photo and photo.size>1024*1024:
            raise ValidationError('A foto deve ter no máximo 1 MB.')
        if photo:
            try:
                im=Image.open(photo)
                im.verify()
                photo.seek(0)
            except (UnidentifiedImageError, OSError, ValueError):
                raise ValidationError('Escolha uma imagem JPG ou PNG válida.')
        return photo
    def save(self, commit=True):
        obj=super().save(commit=False)
        photo=self.cleaned_data.get('upload_photo')
        if photo:
            im=Image.open(photo)
            im.thumbnail((600,600))
            out=BytesIO()
            im.convert('RGB').save(out,format='JPEG',quality=80)
            obj.photo_data=out.getvalue()
            obj.photo_type='image/jpeg'
        if commit: obj.save()
        return obj

@require_http_methods(['GET','POST'])
def sign_in(request):
    if is_admin(request.user): return redirect('manage_dashboard')
    if request.method=='POST':
        user=authenticate(request,username=request.POST.get('username',''),password=request.POST.get('password',''))
        if user and is_admin(user):
            login(request,user)
            return redirect('manage_dashboard')
        messages.error(request,'Usuário ou senha incorretos.')
    return render(request,'votacao/manage/login.html')

@require_POST
@admin_required
def sign_out(request):
    logout(request)
    return redirect('manage_login')

@admin_required
def dashboard(request):
    election=Election.objects.first()
    return render(request,'votacao/manage/dashboard.html',{
        'election':election,
        'candidates':election.candidates.all() if election else [],
        'votes_count':election.votes.count() if election else 0})

@admin_required
@require_http_methods(['GET','POST'])
def edit_election(request):
    election=Election.objects.first()
    if election and election.status!=Election.DRAFT:
        messages.error(request,'A eleição não pode ser alterada depois de iniciada.')
        return redirect('manage_dashboard')
    form=ElectionForm(request.POST or None, instance=election)
    if request.method=='POST' and form.is_valid():
        try:
            with transaction.atomic():
                locked=Election.objects.select_for_update().first()
                if locked and locked.status!=Election.DRAFT:
                    raise ValidationError('A eleição já foi iniciada.')
                obj=form.save(commit=False)
                if locked: obj.pk=locked.pk
                obj.save()
            messages.success(request,'Dados da eleição salvos!')
            return redirect('manage_dashboard')
        except ValidationError as e: form.add_error(None,e)
    return render(request,'votacao/manage/form.html',{'form':form,'page_title':'Criar eleição' if not election else 'Editar eleição','submit_label':'Salvar eleição'})

@admin_required
@require_http_methods(['GET','POST'])
def candidate_form(request, pk=None):
    election=Election.objects.first()
    if not election:
        messages.error(request,'Primeiro, crie a eleição.')
        return redirect('manage_dashboard')
    if election.status!=Election.DRAFT:
        messages.error(request,'O cadastro de candidatos está bloqueado.')
        return redirect('manage_dashboard')
    candidate=get_object_or_404(Candidate,pk=pk,election=election) if pk else None
    form=CandidateForm(request.POST or None,request.FILES or None,instance=candidate)
    if request.method=='POST' and form.is_valid():
        try:
            with transaction.atomic():
                locked=Election.objects.select_for_update().get(pk=election.pk)
                if locked.status!=Election.DRAFT:
                    raise ValidationError('A votação já começou: cadastro bloqueado.')
                obj=form.save(commit=False)
                obj.election=locked
                obj.save()
            messages.success(request,'Candidato salvo com sucesso!')
            return redirect('manage_dashboard')
        except ValidationError as e:form.add_error(None,e)
    return render(request,'votacao/manage/form.html',{'form':form,'page_title':'Editar candidato' if candidate else 'Adicionar candidato','submit_label':'Salvar candidato','candidate':candidate})

@admin_required
@require_POST
def delete_candidate(request, pk):
    with transaction.atomic():
        election=Election.objects.select_for_update().first()
        if not election or election.status!=Election.DRAFT:
            messages.error(request,'Não é possível remover candidatos após iniciar a votação.')
        else:
            candidate=get_object_or_404(Candidate,pk=pk,election=election)
            candidate.delete()
            messages.success(request,'Candidato removido.')
    return redirect('manage_dashboard')

@admin_required
@require_POST
def change_status(request, action):
    if request.POST.get('confirm')!='sim':
        messages.error(request,'Confirmação inválida.')
        return redirect('manage_dashboard')
    with transaction.atomic():
        election=Election.objects.select_for_update().first()
        if not election:
            messages.error(request,'Crie uma eleição primeiro.')
        elif action=='iniciar' and election.status==Election.DRAFT and election.candidates.exists():
            election.status=Election.OPEN
            election.started_at=timezone.now()
            election.save()
            messages.success(request,'Votação iniciada! Os candidatos estão bloqueados.')
        elif action=='encerrar' and election.status==Election.OPEN:
            election.status=Election.CLOSED
            election.ended_at=timezone.now()
            election.save()
            messages.success(request,'Votação encerrada. Os votos foram preservados.')
        else:
            messages.error(request,'Esta ação não está disponível no momento.')
    return redirect('manage_dashboard')
