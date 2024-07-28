from flask import Flask, request, render_template, redirect, url_for, flash
import firebase_admin
from firebase_admin import credentials, db
from ftplib import FTP
from io import BytesIO
import uuid
import google.generativeai as gmeni
from credenciais import *  # Certifique-se de ter um arquivo credenciais.py com suas credenciais

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Defina uma chave secreta para usar com flash messages

# Inicialização do Firebase
cred = credentials.Certificate('fir-6f35e-firebase-adminsdk-5mjto-cb4d3788c7.json')
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://fir-6f35e.firebaseio.com/'
})

# Configuração da API do Google GenerativeAI
gmeni.configure(api_key=API_KEY)

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
    ftp = FTP("ftpupload.net", "if0_36660217", "VV6z1ZhDuhKApb")
    html_file = BytesIO(html_content.encode('utf-8'))
    html_file.seek(0)
    ftp.storbinary(f"STOR /htdocs/{file_name}", html_file)
    ftp.quit()

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

        # Gravar dados no Firebase Realtime Database
        ref = db.reference('guiadebairro')
        ref.push(data)

        flash('Estabelecimento cadastrado com sucesso!')
        return redirect(url_for('index'))

    return render_template('index.html')

@app.route('/search', methods=['GET'])
def search():
    pesquisa_nome = request.args.get('pesquisa_nome', '')
    ref = db.reference('guiadebairro')
    estabelecimentos = ref.get()
    tabela_estabelecimentos = []

    if estabelecimentos:
        for key, dados in estabelecimentos.items():
            if pesquisa_nome.lower() in dados['nome'].lower():
                tabela_estabelecimentos.append(dados)

    return render_template('search.html', estabelecimentos=tabela_estabelecimentos, pesquisa_nome=pesquisa_nome)

if __name__ == "__main__":
    app.run(debug=True)
