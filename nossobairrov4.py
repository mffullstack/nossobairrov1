from flask import Flask, request, render_template, redirect, url_for, flash, session
import uuid
import google.generativeai as gmeni
from credenciais import *  # Certifique-se de ter um arquivo credenciais.py com suas credenciais
from supabase import create_client, Client
from ftplib import FTP
from io import BytesIO
import bcrypt
import requests

app = Flask(__name__)
app.secret_key = secret_key_supa

# Inicialização do Supabase
supabase_url = supabase_url
supabase_key = supabase_key
supabase: Client = create_client(supabase_url, supabase_key)

# Configuração da API do Google GenerativeAI
gmeni.configure(api_key=API_KEY_gemeni)

def get_lat_long_from_address(address):
    """Obtém latitude e longitude a partir do endereço usando a API Nominatim."""
    try:
        response = requests.get(
            f"https://nominatim.openstreetmap.org/search",
            params={
                "q": address,
                "format": "json",
                "addressdetails": 1
            }
        )
        data = response.json()
        if data:
            lat = data[0].get('lat')
            lon = data[0].get('lon')
            return lat, lon
        return None, None
    except Exception as e:
        print(f"Erro ao buscar coordenadas: {e}")
        return None, None

def generate_and_save_html(descricao_estabelecimento):
    model = gmeni.GenerativeModel('gemini-pro')
    input_text = f"Crie uma landing page simples voltada para esse tipo de negócio {descricao_estabelecimento}, utilizando HTML e com as sessões início, sobre nós e contato respectivamente. O CSS precisa ser escrito no mesmo arquivo"
    response = model.generate_content(input_text)
    generated_html = response.text
    # Remove caracteres desnecessários
    generated_html = generated_html.replace("html", "").replace("", "")
    file_name = str(uuid.uuid4()) + ".html"
    with open(file_name, "w", encoding="utf-8") as html_file:
        html_file.write(generated_html)
    return generated_html, file_name

def check_and_send_html_to_ftp(html_content, file_name):
    try:
        # Conecta ao servidor FTP com as credenciais fornecidas
        ftp = FTP("ftp.nossobairro.app.br", "sites@nossobairro.app.br", "@Equipe123")
        
        # Converte o conteúdo HTML em bytes
        html_file = BytesIO(html_content.encode('utf-8'))
        html_file.seek(0)
        
        # Altera o diretório para a pasta desejada (substitua pelo caminho correto)
        #ftp.cwd("/htdocs/nossobairro.app.br/sites/")
        
        # Envia o arquivo para a pasta especificada
        ftp.storbinary(f"STOR {file_name}", html_file)
        
        # Fecha a conexão com o servidor FTP
        ftp.quit()
    except Exception as e:
        print(f"Erro ao enviar o arquivo para o FTP: {e}")

def save_to_supabase(data):
    try:
        response = supabase.table('guiadebairro').insert(data).execute()
        return bool(response.data)
    except Exception as e:
        print(f"Erro ao salvar dados no Supabase: {e}")
        return False

def update_supabase(data, id):
    try:
        response = supabase.table('guiadebairro').update(data).eq('id', id).execute()
        return bool(response.data)
    except Exception as e:
        print(f"Erro ao atualizar dados no Supabase: {e}")
        return False

def check_user_credentials(email, password):
    try:
        response = supabase.table('usuarios').select('senha').eq('email', email).execute()
        user = response.data
        if not user:
            return False

        hashed_password = user[0]['senha'].encode('utf-8')
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password)
    except Exception as e:
        print(f"Erro ao verificar credenciais: {e}")
        return False

def register_user(email, password):
    try:
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        response = supabase.table('usuarios').insert({
            'email': email,
            'senha': hashed_password.decode('utf-8'),
            'plano': 'free'  # Define o plano como 'free' para novos usuários
        }).execute()
        return bool(response.data)
    except Exception as e:
        print(f"Erro ao registrar usuário: {e}")
        return False

def login_required(f):
    """Decorator to ensure that the user is logged in before accessing the route."""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == 'POST':
        nome = request.form.get('nome')
        endereco = request.form.get('endereco')
        site = request.form.get('site')
        descricao = request.form.get('descricao')
        gerar_site = request.form.get('gerar_site')

        # Novos campos
        horario_funcionamento = request.form.get('horario_funcionamento')
        contato = request.form.get('contato')
        redes_sociais = request.form.get('redes_sociais')
        tipo_servico_produto = request.form.get('tipo_servico_produto')
        metodos_pagamento = request.form.get('metodos_pagamento')
        como_chegar = request.form.get('como_chegar')
        sobre_estabelecimento = request.form.get('sobre_estabelecimento')  # Novo campo

        imagem = request.form.get('imagem')
        categoria = request.form.get('categoria')

        if not nome or not endereco:
            flash('Nome e endereço são obrigatórios!')
            return redirect(url_for('index'))

        # Buscar latitude e longitude
        latitude, longitude = get_lat_long_from_address(endereco)
        if not latitude or not longitude:
            flash('Não foi possível obter coordenadas para o endereço fornecido.')
            return redirect(url_for('index'))

        if gerar_site == 'sim':
            if not descricao or not descricao.strip():
                flash('Por favor, preencha a descrição do negócio!')
                return redirect(url_for('index'))
            generated_html, file_name = generate_and_save_html(descricao)
            check_and_send_html_to_ftp(generated_html, file_name)
            site = f"http://meustestes.42web.io/{file_name}"

        data = {
            'nome': nome,
            'categoria': categoria,
            'endereco': endereco,
            'imagem': imagem,
            'site': site,
            'patrocinado': request.form.get('patrocinado', 'nao') == 'sim',
            'email_usuario': session['user'],
            'horario_funcionamento': horario_funcionamento,
            'contato': contato,
            'redes_sociais': redes_sociais,
            'tipo_servico_produto': tipo_servico_produto,
            'metodos_pagamento': metodos_pagamento,
            #'como_chegar': como_chegar,
            'sobre_estabelecimento': sobre_estabelecimento,  # Incluindo o novo campo
            'latitude': latitude,
            'longitude': longitude,
            'oculto': False  # Define o estado inicial como não oculto
        }

        success = save_to_supabase(data)

        if success:
            flash('Estabelecimento cadastrado com sucesso!')
        else:
            flash('Erro ao cadastrar estabelecimento.')

        return redirect(url_for('index'))

    return render_template('index.html')

@app.route('/search', methods=['GET'])
@login_required
def search():
    pesquisa_nome = request.args.get('pesquisa_nome', '')
    try:
        response = supabase.table('guiadebairro').select("*").eq('oculto', False).execute()
        estabelecimentos = response.data
        tabela_estabelecimentos = []

        if estabelecimentos:
            for dados in estabelecimentos:
                if pesquisa_nome.lower() in dados['nome'].lower():
                    tabela_estabelecimentos.append(dados)

        # Ordenar estabelecimentos com patrocinados primeiro
        tabela_estabelecimentos.sort(key=lambda x: (not x['patrocinado'], x['nome']))

    except Exception as e:
        print(f"Erro ao buscar estabelecimentos: {e}")
        tabela_estabelecimentos = []

    return render_template('search.html', estabelecimentos=tabela_estabelecimentos, pesquisa_nome=pesquisa_nome)

@app.route('/meus-estabelecimentos', methods=['GET'])
@login_required
def meus_estabelecimentos():
    user_email = session.get('user')
    try:
        response = supabase.table('guiadebairro').select('*').eq('email_usuario', user_email).execute()
        estabelecimentos = response.data
    except Exception as e:
        print(f"Erro ao buscar meus estabelecimentos: {e}")
        estabelecimentos = []

    return render_template('meus_estabelecimentos.html', estabelecimentos=estabelecimentos)

@app.route('/editar_estabelecimento/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_estabelecimento(id):
    if request.method == 'POST':
        nome = request.form.get('nome')
        endereco = request.form.get('endereco')
        imagem = request.form.get('imagem')
        descricao = request.form.get('descricao')
        categoria = request.form.get('categoria')
        patrocinado = 'patrocinado' in request.form

        # Novos campos
        horario_funcionamento = request.form.get('horario_funcionamento')
        contato = request.form.get('contato')
        redes_sociais = request.form.get('redes_sociais')
        tipo_servico_produto = request.form.get('tipo_servico_produto')
        metodos_pagamento = request.form.get('metodos_pagamento')
        como_chegar = request.form.get('como_chegar')
        sobre_estabelecimento = request.form.get('sobre_estabelecimento')  # Novo campo

        # Buscar latitude e longitude do novo endereço
        latitude, longitude = get_lat_long_from_address(endereco)

        # Atualizar o estabelecimento no Supabase
        data = {
            'nome': nome,
            'endereco': endereco,
            'imagem': imagem,
            'patrocinado': patrocinado,
            'categoria': categoria,
            'horario_funcionamento': horario_funcionamento,
            'contato': contato,
            'redes_sociais': redes_sociais,
            'tipo_servico_produto': tipo_servico_produto,
            'metodos_pagamento': metodos_pagamento,
            'como_chegar': como_chegar,
            'sobre_estabelecimento': sobre_estabelecimento,  # Atualizando o campo
            'latitude': latitude,
            'longitude': longitude
        }

        success = update_supabase(data, id)

        if success:
            flash('Estabelecimento atualizado com sucesso!')
        else:
            flash('Erro ao atualizar estabelecimento.')

        return redirect(url_for('meus_estabelecimentos'))

    # Buscar o estabelecimento pelo ID
    estabelecimento = supabase.table('guiadebairro').select('*').eq('id', id).execute()
    return render_template('editar_estabelecimento.html', estabelecimento=estabelecimento.data[0])

@app.route('/ocultar_estabelecimento/<int:id>', methods=['POST'])
@login_required
def ocultar_estabelecimento(id):
    try:
        response = supabase.table('guiadebairro').update({'oculto': True}).eq('id', id).execute()
        if response.data:
            flash('Estabelecimento oculto com sucesso!')
        else:
            flash('Erro ao ocultar estabelecimento.')
    except Exception as e:
        print(f"Erro ao ocultar estabelecimento: {e}")
        flash('Erro ao ocultar estabelecimento.')

    return redirect(url_for('meus_estabelecimentos'))

@app.route('/mostrar_estabelecimento/<int:id>', methods=['POST'])
@login_required
def mostrar_estabelecimento(id):
    try:
        # Atualizar o estado do estabelecimento para não oculto
        response = supabase.table('guiadebairro').update({'oculto': False}).eq('id', id).execute()
        if response.data:
            flash('Estabelecimento visível novamente!')
        else:
            flash('Erro ao tornar o estabelecimento visível.')
    except Exception as e:
        print(f"Erro ao mostrar o estabelecimento: {e}")
        flash('Erro ao mostrar o estabelecimento.')

    return redirect(url_for('meus_estabelecimentos'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')

        if not email or not senha:
            flash('Email e senha são obrigatórios!')
            return redirect(url_for('login'))

        if check_user_credentials(email, senha):
            session['user'] = email
            return redirect(url_for('index'))
        else:
            flash('Credenciais inválidas!')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')

        if not email or not senha:
            flash('Email e senha são obrigatórios!')
            return redirect(url_for('register'))

        if register_user(email, senha):
            flash('Registro bem-sucedido! Você pode fazer login.')
            return redirect(url_for('login'))
        else:
            flash('Erro ao registrar usuário.')

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/perfil', methods=['GET'])
@login_required
def perfil():
    user_email = session.get('user')
    try:
        response = supabase.table('usuarios').select('email', 'plano').eq('email', user_email).execute()
        user_data = response.data[0] if response.data else {'email': user_email, 'plano': 'free'}
    except Exception as e:
        print(f"Erro ao buscar dados do usuário: {e}")
        user_data = {'email': user_email, 'plano': 'free'}

    return render_template('perfil.html', email=user_data['email'], plano=user_data['plano'])

@app.route('/upgrade', methods=['POST'])
@login_required
def upgrade():
    user_email = session.get('user')
    try:
        response = supabase.table('usuarios').update({'plano': 'premium'}).eq('email', user_email).execute()
        if response.data:
            flash('Plano atualizado para Premium!')
        else:
            flash('Erro ao atualizar o plano.')
    except Exception as e:
        print(f"Erro ao atualizar o plano: {e}")
        flash('Erro ao atualizar o plano.')

    return redirect(url_for('perfil'))

@app.route('/downgrade', methods=['POST'])
@login_required
def downgrade():
    user_email = session.get('user')
    try:
        response = supabase.table('usuarios').update({'plano': 'free'}).eq('email', user_email).execute()
        if response.data:
            flash('Plano revertido para Free!')
        else:
            flash('Erro ao reverter o plano.')
    except Exception as e:
        print(f"Erro ao reverter o plano: {e}")
        flash('Erro ao reverter o plano.')

    return redirect(url_for('perfil'))

if __name__ == "__main__":
    app.run(debug=True)
