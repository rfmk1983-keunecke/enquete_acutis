from django import forms
from .models import Vote
class VoteForm(forms.Form):
    voter_name=forms.CharField(label='Seu nome completo',max_length=150,widget=forms.TextInput(attrs={'autocomplete':'name','placeholder':'Nome completo'}))
    voter_email=forms.EmailField(label='Seu e-mail',widget=forms.EmailInput(attrs={'autocomplete':'email','placeholder':'seuemail@exemplo.com'}))
    candidate=forms.IntegerField(widget=forms.HiddenInput)
    consent=forms.BooleanField(label='Estou ciente de que meus dados serão registrados para controle e auditoria da votação.')
    def clean_voter_email(self):return self.cleaned_data['voter_email'].strip().lower()
