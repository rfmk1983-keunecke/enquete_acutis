# Eleição Escolar — Django

## Funcionalidades
- Painel `/admin/` para administrador, eleição e candidatos.
- Fotos armazenadas no **banco de dados** (sem depender do disco efêmero do Render).
- Ação administrativa **INICIAR** bloqueia cadastros; **ENCERRAR** bloqueia novos votos. Não reabre.
- Um voto por e-mail normalizado, garantido por restrição UNIQUE no banco.
- Candidato não pode votar usando o próprio e-mail cadastrado.
- Registra eleitor, candidato, horário, IP e navegador.
- Painel privado `/painel/resultado/` e CSV privado `/painel/auditoria.csv`.
- Votos não podem ser editados/excluídos pelo painel.

## Implantação gratuita recomendada
1. Crie projeto em [Supabase](https://supabase.com/), obtenha conexão PostgreSQL com SSL. Prefira o pooler em **session mode** com IPv4 caso necessário; configure a `DATABASE_URL` fornecida.
2. Suba esta pasta para um repositório **privado** no [GitHub](https://github.com/). Não publique `.env`.
3. No [Render](https://render.com/), crie **New > Web Service**, conecte o GitHub, runtime **Python**, plano Free.
4. Build command: `bash build.sh`. Start command: `bash start.sh`.
5. Configure no ambiente Render: `DATABASE_URL`, `SECRET_KEY` (uma string longa aleatória), `ALLOWED_HOSTS=nomedosite.onrender.com`, `CSRF_TRUSTED_ORIGINS=https://nomedosite.onrender.com`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `ADMIN_EMAIL`, `DEBUG=false`.
6. Faça deploy; acesse `https://nomedosite.onrender.com/admin/`.
7. Crie uma eleição e depois os candidatos, com nome, e-mail, número e foto. Na lista de eleições, marque a eleição e use **Ações > INICIAR eleição**.
8. Compartilhe a URL com os alunos; após o fim, use **Ações > ENCERRAR eleição**. Consulte resultados e exporte auditoria.

**IMPORTANTE**: Render Free adormece após 15 min de inatividade e o próximo acesso pode demorar. O filesystem do Render é efêmero, não use SQLite lá. O Supabase Free pode pausar após 7 dias de inatividade e não disponibiliza backups automáticos: exporte periodicamente o CSV e mantenha backup do banco.

## Uso local
```bash
python -m venv .venv
# ative o ambiente virtual
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```
Acesse `http://127.0.0.1:8000/admin/`.

## Limitações de segurança e privacidade
- **E-mail digitado não é identidade verificada.** Uma pessoa pode usar outro e-mail e votar novamente ou se passar por candidato. Para eleição com exigência real de integridade, introduza cadastro prévio de eleitores, autenticação com código por e-mail ou conta escolar verificada.
- O IP registrado é o endereço de conexão visto pela aplicação, podendo corresponder a proxy/Render; cabeçalhos encaminhados não são aceitos cegamente.
- Administrador com acesso direto ao banco pode alterar registros; CSV é evidência de auditoria simples, não trilha criptográfica imutável.
- Para uso com menores, obtenha autorização/validação da escola, minimize dados, restrinja acesso e estabeleça prazo de retenção e exclusão, observando a LGPD. Não divulgue a lista de votos nem fotos sem autorização.
- Um e-mail só pode votar uma vez, mesmo se pertencer a candidato; candidatos podem votar em outras pessoas.


## NOVO PAINEL SIMPLIFICADO (v2)

- Abra `https://SEU-SITE.onrender.com/gestao/` e entre com as mesmas credenciais do administrador anterior.
- Configure a eleição, cadastre/edite/exclua candidatos, inicie ou encerre a votação e acesse os resultados/auditoria.
- O Django Admin original continua acessível em `/admin/`, mas não é necessário para a operação normal.
- **Atualização segura:** substitua/adicione os arquivos desta versão no repositório existente; mantenha `DATABASE_URL` e demais variáveis. Não apague o banco Supabase nem execute `flush`.
- Se o GitHub tiver os arquivos dentro de uma pasta `eleicao_escolar`, copie os arquivos preservando esta estrutura. Se estiverem na raiz, copie o conteúdo interno da pasta.
- Execute testes com eleitores fictícios antes de liberar à escola. A identidade dos eleitores por nome/e-mail ainda não é verificada.


## Reiniciar eleição de teste (painel v3)

Acesse `/gestao/` → **Gerenciar reinício da votação** (ou `/gestao/reiniciar/`).
Faça download da auditoria antes, digite `REINICIAR` e informe a senha do usuário logado.
O sistema apaga definitivamente os votos desta eleição, remove as datas de início e fim,
retorna ao estado Preparação e mantém candidatos/fotos.
Não apaga o banco PostgreSQL, usuários ou configurações. Esta operação não tem desfazer.

Atualize o mesmo repositório GitHub; não altere as variáveis do Render/Supabase.
