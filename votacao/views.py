import csv
from django.contrib.admin.views.decorators import staff_member_required
from django.db import IntegrityError,transaction
from django.db.models import Count
from django.http import Http404,HttpResponse
from django.shortcuts import redirect,render,get_object_or_404
from django.views.decorators.http import require_http_methods
from .models import Candidate,Election,Vote
from .forms import VoteForm

def current():return Election.objects.first()
def home(request):
    election=current()
    return render(request,'votacao/home.html',{'election':election,'candidates':election.candidates.all() if election else []})
@require_http_methods(['GET','POST'])
def vote(request):
    election=current()
    if not election or election.status!=Election.OPEN:return redirect('home')
    form=VoteForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        candidate=Candidate.objects.filter(pk=form.cleaned_data['candidate'],election=election).first()
        email=form.cleaned_data['voter_email']
        if candidate is None:form.add_error(None,'Candidato inválido.')
        elif candidate.email==email:form.add_error(None,'Você não pode votar em si mesmo.')
        elif Vote.objects.filter(election=election,voter_email=email).exists():form.add_error(None,'Este e-mail já registrou um voto.')
        else:
            try:
                with transaction.atomic():
                    # Lock election row in PostgreSQL: closing and voting are serialized.
                    locked=Election.objects.select_for_update().get(pk=election.pk)
                    if locked.status != Election.OPEN:form.add_error(None,'A votação foi encerrada.')
                    else:
                        Vote.objects.create(election=locked,candidate=candidate,voter_name=form.cleaned_data['voter_name'].strip(),voter_email=email,ip_address=request.META.get('REMOTE_ADDR'),user_agent=request.META.get('HTTP_USER_AGENT','')[:400])
                        request.session['voted_successfully']=True
                        return redirect('success')
            except IntegrityError:form.add_error(None,'Este e-mail já registrou um voto.')
    return render(request,'votacao/vote.html',{'election':election,'candidate_list':election.candidates.all(),'form':form})
def success(request):
    if not request.session.pop('voted_successfully',False):return redirect('home')
    return render(request,'votacao/success.html')
def photo(request,pk):
    candidate=get_object_or_404(Candidate,pk=pk)
    if not candidate.photo_data:raise Http404()
    response=HttpResponse(bytes(candidate.photo_data),content_type=candidate.photo_type)
    response['Cache-Control']='public, max-age=3600'
    response['X-Content-Type-Options']='nosniff'
    return response
@staff_member_required
def results(request):
    election=current()
    candidates=election.candidates.annotate(total=Count('votes')).order_by('-total','number') if election else []
    return render(request,'votacao/results.html',{'election':election,'candidates':candidates,'total':election.votes.count() if election else 0})
@staff_member_required
def export_csv(request):
    response=HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition']='attachment; filename="auditoria_eleicao.csv"'
    response.write('\ufeff')
    writer=csv.writer(response,delimiter=';')
    writer.writerow(['ID voto','Eleição','Nome eleitor','E-mail eleitor','Número candidato','Nome candidato','E-mail candidato','Data/hora UTC','IP','Navegador'])
    for v in Vote.objects.select_related('election','candidate').order_by('id').iterator():
        writer.writerow([v.pk,v.election.title,v.voter_name,v.voter_email,v.candidate.number,v.candidate.name,v.candidate.email,v.created_at.isoformat(),v.ip_address or '',v.user_agent])
    return response
