from flask import Flask, request, render_template, redirect, url_for, flash, session
import uuid
import google.generativeai as gmeni
from credenciais import *  # Certifique-se de ter um arquivo credenciais.py com suas credenciais
from supabase import create_client, Client
from ftplib import FTP
from io import BytesIO
import bcrypt

app = Flask(__name__)
app.secret_key = secret_key_supa

# Inicialização do Supabase
supabase_url = supabase_url
supabase_key = supabase_key
supabase: Client = create_client(supabase_url, supabase_key)

# Configuração da API do Google GenerativeAI
gmeni.configure(api_key=API_KEY_gemeni)

def generate_and_save_html(descricao_estabelecimento):
    model = gmeni.GenerativeModel('gemini-pro')
    input_text = f"Crie uma landing page simples voltada para esse tipo de negócio {descricao_estabelecimento}, utilizando HTML e com as sessões início, sobre nós e contato respectivamente. O CSS precisa ser escrito no mesmo arquivo"
    response = model.generate_content(input_text)
    generated_html = response.text
    generated_html = generated_html.replace("html", "").replace("", "")
    file_name = str(uuid.uuid4()) + ".html"
    with open(file_name, "w", encoding="utf-8") as html_file:
        html_file.write(generated_html)
    return generated_html, file_name

def check_and_send_html_to_ftp(html_content, file_name):
    try:
        ftp = FTP("ftpupload.net", "if0_36660217", "VV6z1ZhDuhKApb")  # Substitua pelas suas credenciais FTP
        html_file = BytesIO(html_content.encode('utf-8'))
        html_file.seek(0)
        ftp.storbinary(f"STOR /htdocs/{file_name}", html_file)
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
        response = supabase.table('usuarios').insert({'email': email, 'senha': hashed_password.decode('utf-8')}).execute()
        return bool(response.data)
    except Exception as e:
        print(f"Erro ao registrar usuário: {e}")
        return False

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        nome = request.form.get('nome')
        endereco = request.form.get('endereco')
        site = request.form.get('site')
        descricao = request.form.get('descricao')
        gerar_site = request.form.get('gerar_site')
        imagem = request.form.get('imagem')

        if not nome or not endereco:
            flash('Nome e endereço são obrigatórios!')
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
            'endereco': endereco,
            'imagem': imagem,
            'site': site
        }

        # Gravar dados no Supabase
        success = save_to_supabase(data)

        if success:
            flash('Estabelecimento cadastrado com sucesso!')
        else:
            flash('Erro ao cadastrar estabelecimento.')

        return redirect(url_for('index'))

    return render_template('index.html')

@app.route('/search', methods=['GET'])
def search():
    pesquisa_nome = request.args.get('pesquisa_nome', '')
    try:
        response = supabase.table('guiadebairro').select("*").execute()
        estabelecimentos = response.data
        tabela_estabelecimentos = []

        if estabelecimentos:
            for dados in estabelecimentos:
                if pesquisa_nome.lower() in dados['nome'].lower():
                    tabela_estabelecimentos.append(dados)

    except Exception as e:
        print(f"Erro ao buscar estabelecimentos: {e}")
        tabela_estabelecimentos = []

    return render_template('search.html', estabelecimentos=tabela_estabelecimentos, pesquisa_nome=pesquisa_nome)

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

if __name__ == "__main__":
    app.run(debug=True)