API_GROK = "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"

from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash
from PIL import Image, ImageDraw, ImageFont
import hashlib
import requests
from io import BytesIO
import os

app = Flask(__name__)
app.secret_key = 's3cr3t_k3y'  # Defina uma chave secreta para flash messages

# Diretório para salvar os logotipos gerados
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Função para converter hexadecimal para RGB
def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

# Função para baixar a fonte do Google Fonts
def download_font(font_name):
    font_urls = {
        "Montserrat": "https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700&display=swap",
        "Lobster": "https://fonts.googleapis.com/css2?family=Lobster&display=swap",
        "Roboto": "https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap",
        "Playfair Display": "https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&display=swap",
        "Raleway": "https://fonts.googleapis.com/css2?family=Raleway:wght@400;700&display=swap",
        "Bebas Neue": "https://fonts.googleapis.com/css2?family=Bebas+Neue&display=swap",
        "Oswald": "https://fonts.googleapis.com/css2?family=Oswald:wght@400;700&display=swap",
        "Poppins": "https://fonts.googleapis.com/css2?family=Poppins:wght@400;700&display=swap",
        "Open Sans": "https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;700&display=swap",
        "Merriweather": "https://fonts.googleapis.com/css2?family=Merriweather:wght@400;700&display=swap",
        "Noto Sans": "https://fonts.googleapis.com/css2?family=Noto+Sans:wght@400;700&display=swap",
        "Source Sans Pro": "https://fonts.googleapis.com/css2?family=Source+Sans+Pro:wght@400;700&display=swap",
        "Lora": "https://fonts.googleapis.com/css2?family=Lora:wght@400;700&display=swap",
        "Inconsolata": "https://fonts.googleapis.com/css2?family=Inconsolata:wght@400&display=swap",
        "Fira Sans": "https://fonts.googleapis.com/css2?family=Fira+Sans:wght@400;700&display=swap",
        "PT Sans": "https://fonts.googleapis.com/css2?family=PT+Sans:wght@400;700&display=swap",
        "Quicksand": "https://fonts.googleapis.com/css2?family=Quicksand:wght@400;700&display=swap",
        "Nunito": "https://fonts.googleapis.com/css2?family=Nunito:wght@400;700&display=swap",
        "Cabin": "https://fonts.googleapis.com/css2?family=Cabin:wght@400;700&display=swap",
        "Anton": "https://fonts.googleapis.com/css2?family=Anton&display=swap",
        "Dancing Script": "https://fonts.googleapis.com/css2?family=Dancing+Script:wght@400;700&display=swap",
        "Great Vibes": "https://fonts.googleapis.com/css2?family=Great+Vibes&display=swap",
        "Raleway Dots": "https://fonts.googleapis.com/css2?family=Raleway+Dots&display=swap",
        "Yesteryear": "https://fonts.googleapis.com/css2?family=Yesteryear&display=swap",
        "Tangerine": "https://fonts.googleapis.com/css2?family=Tangerine:wght@400;700&display=swap",
        "Righteous": "https://fonts.googleapis.com/css2?family=Righteous&display=swap",
        "Zilla Slab": "https://fonts.googleapis.com/css2?family=Zilla+Slab:wght@400;700&display=swap",
        "Monda": "https://fonts.googleapis.com/css2?family=Monda:wght@400;700&display=swap",
        "Libre Baskerville": "https://fonts.googleapis.com/css2?family=Libre+Baskerville:wght@400;700&display=swap",
        "Varela Round": "https://fonts.googleapis.com/css2?family=Varela+Round&display=swap",
        "Arvo": "https://fonts.googleapis.com/css2?family=Arvo:wght@400;700&display=swap",
        
    }
    try:
        font_url = font_urls.get(font_name, font_urls["Roboto"])
        response = requests.get(font_url)
        css = response.text
        font_url_start = css.find("url(") + 4
        font_url_end = css.find(")", font_url_start)
        if font_url_start == -1 or font_url_end == -1:
            raise ValueError("URL da fonte não encontrada no CSS.")
        font_url = css[font_url_start:font_url_end].strip('"').strip("'")
        
        font_response = requests.get(font_url)
        return BytesIO(font_response.content)
    except Exception as e:
        print(f"Erro ao baixar a fonte: {e}")
        raise

# Função para gerar um identificador único
def generate_unique_identifier(seed):
    return hashlib.md5(seed.encode()).hexdigest()

# Função para gerar o logotipo
def generate_unique_logo(company_name, slogan, font_name, background_color, text_color, social_links, base_width=800, base_height=400, font_size=60):
    try:
        font_file = download_font(font_name)
        font = ImageFont.truetype(font_file, font_size)
        
        # Criar imagem para calcular o tamanho do texto
        img = Image.new('RGB', (base_width, base_height), background_color)
        draw = ImageDraw.Draw(img)
        
        name_width, name_height = draw.textsize(company_name, font=font)
        slogan_width, slogan_height = draw.textsize(slogan, font=font)
        
        # Adicionar palavras das redes sociais e "Telefone"
        social_media = social_links.splitlines()
        social_media_widths = [draw.textsize(sm, font=font)[0] for sm in social_media]
        social_media_heights = [draw.textsize(sm, font=font)[1] for sm in social_media]
        
        # Ajustar a largura e altura da imagem para acomodar o texto e o espaçamento
        logo_width = max(base_width, max(name_width, slogan_width, sum(social_media_widths) + 80) + 40)
        logo_height = max(base_height, name_height + slogan_height + max(social_media_heights) + 80)  # Ajustar a altura
        
        img = Image.new('RGB', (logo_width, logo_height), background_color)
        draw = ImageDraw.Draw(img)
        
        # Ajustar a posição do texto
        name_position = ((logo_width - name_width) / 2, (logo_height - name_height - slogan_height - max(social_media_heights) - 30) / 2 - 10)
        slogan_position = ((logo_width - slogan_width) / 2, name_position[1] + name_height + 30)
        
        # Adicionar textos à imagem
        draw.text(name_position, company_name, fill=text_color, font=font)
        draw.text(slogan_position, slogan, fill=text_color, font=font)
        
        # Adicionar palavras das redes sociais e "Telefone" lado a lado
        total_social_width = sum(social_media_widths)
        space_between = (logo_width - total_social_width) / (len(social_media) + 1)
        x_position = space_between
        
        for sm in social_media:
            sm_width = draw.textsize(sm, font=font)[0]
            sm_position = (x_position, slogan_position[1] + slogan_height + 20)
            draw.text(sm_position, sm, fill=text_color, font=font)
            x_position += sm_width + space_between
        
        return img
    except Exception as e:
        print(f"Erro ao gerar o logotipo: {e}")
        raise

@app.route('/art', methods=['GET', 'POST'])
def art():
    if request.method == 'POST':
        company_name = request.form['company_name']
        slogan = request.form['slogan']
        font_name = request.form['font']
        background_color_hex = request.form['background_color']
        text_color_hex = request.form['text_color']
        social_links = request.form['social_links']
        
        # Converter cores hexadecimais para RGB
        background_color = hex_to_rgb(background_color_hex)
        text_color = hex_to_rgb(text_color_hex)
        
        try:
            logo = generate_unique_logo(company_name, slogan, font_name, background_color, text_color, social_links)
            identifier = generate_unique_identifier(company_name + slogan)
            filename = f'logo_{identifier}.png'
            logo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            logo.save(logo_path)
            return redirect(url_for('art', filename=filename))
        except Exception as e:
            flash(f'Erro ao gerar o logotipo: {e}', 'danger')
            return redirect(url_for('art'))

    return render_template('art.html')

# Rota para servir arquivos de logotipo gerados
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)


