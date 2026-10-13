from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone

class Election(models.Model):
    DRAFT='draft'; OPEN='open'; CLOSED='closed'
    STATUS=[(DRAFT,'Preparação'),(OPEN,'Em andamento'),(CLOSED,'Encerrada')]
    title=models.CharField('Título',max_length=160,default='Eleição Escolar')
    description=models.CharField('Descrição',max_length=240,blank=True)
    status=models.CharField('Estado',max_length=8,choices=STATUS,default=DRAFT)
    started_at=models.DateTimeField('Início',null=True,blank=True)
    ended_at=models.DateTimeField('Fim',null=True,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    def save(self,*args,**kwargs):
        if self.pk:
            original=Election.objects.get(pk=self.pk)
            if original.status != self.DRAFT and (self.title!=original.title or self.description!=original.description):
                raise ValidationError('Não é permitido alterar a eleição depois de iniciada.')
            transitions={self.DRAFT:{self.DRAFT,self.OPEN},self.OPEN:{self.OPEN,self.CLOSED},self.CLOSED:{self.CLOSED}}
            if self.status not in transitions[original.status]: raise ValidationError('Transição de estado inválida.')
        elif Election.objects.exists(): raise ValidationError('Este projeto permite apenas uma eleição por instalação.')
        super().save(*args,**kwargs)
    def __str__(self):return self.title

class Candidate(models.Model):
    election=models.ForeignKey(Election,on_delete=models.PROTECT,related_name='candidates')
    name=models.CharField('Nome',max_length=150)
    email=models.EmailField('E-mail')
    number=models.PositiveIntegerField('Número de votação')
    photo_data=models.BinaryField('Foto',blank=True,default=bytes,editable=False)
    photo_type=models.CharField(max_length=30,default='image/jpeg',editable=False)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering=['number']
        constraints=[models.UniqueConstraint(fields=['election','email'],name='unique_candidate_email'),models.UniqueConstraint(fields=['election','number'],name='unique_candidate_number')]
    def clean(self):
        self.email=(self.email or '').strip().lower()
        if self.election_id and self.election.status!=Election.DRAFT: raise ValidationError('Cadastro bloqueado após início da votação.')
    def save(self,*args,**kwargs):
        self.full_clean()
        super().save(*args,**kwargs)
    def delete(self,*args,**kwargs):
        if self.election.status!=Election.DRAFT: raise ValidationError('Não é possível excluir candidatos após o início.')
        super().delete(*args,**kwargs)
    def __str__(self):return f'{self.number} — {self.name}'

class Vote(models.Model):
    election=models.ForeignKey(Election,on_delete=models.PROTECT,related_name='votes')
    candidate=models.ForeignKey(Candidate,on_delete=models.PROTECT,related_name='votes')
    voter_name=models.CharField('Nome do eleitor',max_length=150)
    voter_email=models.EmailField('E-mail do eleitor')
    ip_address=models.GenericIPAddressField('IP',null=True,blank=True)
    user_agent=models.CharField('Navegador',max_length=400,blank=True)
    created_at=models.DateTimeField('Data/hora do voto',default=timezone.now,editable=False)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['election','voter_email'],name='one_vote_per_email_per_election')]
        ordering=['-created_at']
    def clean(self):
        self.voter_email=(self.voter_email or '').strip().lower()
        if self.election_id and self.election.status!=Election.OPEN: raise ValidationError('Votação não está aberta.')
        if self.candidate_id and self.candidate.election_id!=self.election_id: raise ValidationError('Candidato fora da eleição.')
        if self.candidate_id and self.candidate.email==self.voter_email:raise ValidationError('Candidatos não podem votar em si mesmos.')
    def save(self,*args,**kwargs):
        if self.pk: raise ValidationError('Votos não podem ser alterados.')
        self.full_clean();super().save(*args,**kwargs)
    def delete(self,*args,**kwargs):raise ValidationError('Votos não podem ser excluídos.')
    def __str__(self):return f'Voto #{self.pk}'
