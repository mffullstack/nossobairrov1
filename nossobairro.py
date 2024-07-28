from flask import Flask, request, render_template, redirect, url_for, flash
import uuid
import google.generativeai as gmeni
from credenciais import *  # Certifique-se de ter um arquivo credenciais.py com suas credenciais
from supabase import create_client, Client
from ftplib import FTP
from io import BytesIO

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
    generated_html = generated_html.replace("```html", "").replace("```", "")
    file_name = str(uuid.uuid4()) + ".html"
    with open(file_name, "w", encoding="utf-8") as html_file:
        html_file.write(generated_html)
    return generated_html, file_name

def check_and_send_html_to_ftp(html_content, file_name):
    ftp = FTP("ftpupload.net", "if0_36660217", "VV6z1ZhDuhKApb")  # Substitua pelas suas credenciais FTP
    html_file = BytesIO(html_content.encode('utf-8'))
    html_file.seek(0)
    ftp.storbinary(f"STOR /htdocs/{file_name}", html_file)
    ftp.quit()

def save_to_supabase(data):
    response = supabase.table('guiadebairro').insert(data).execute()
    # Verifique se a resposta contém dados
    if response.data:
        return True
    else:
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
    response = supabase.table('guiadebairro').select("*").execute()
    estabelecimentos = response.data
    tabela_estabelecimentos = []

    if estabelecimentos:
        for dados in estabelecimentos:
            if pesquisa_nome.lower() in dados['nome'].lower():
                tabela_estabelecimentos.append(dados)

    return render_template('search.html', estabelecimentos=tabela_estabelecimentos, pesquisa_nome=pesquisa_nome)

if __name__ == "__main__":
    app.run(debug=True)

