from flask import Flask, render_template
import requests

app = Flask(__name__)

def get_coordinates(address):
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        'q': address,
        'format': 'json',
        'addressdetails': 1
    }
    response = requests.get(url, params=params)
    data = response.json()
    
    if data:
        location = data[0]
        lat = location['lat']
        lon = location['lon']
        return lat, lon
    return None, None

@app.route('/localizacao')
def localizacao():
    address = "Rua. Benjamin Constant, 67, Rio Branco, Acre "
    latitude, longitude = get_coordinates(address)
    
    if not latitude or not longitude:
        return "Não foi possível encontrar a localização para o endereço fornecido.", 404

    return render_template('localizacao.html', latitude=latitude, longitude=longitude)

if __name__ == "__main__":
    app.run(debug=True)
