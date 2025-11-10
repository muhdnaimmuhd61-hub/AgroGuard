from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

# ===== MULTI-LANGUAGE TRANSLATIONS =====
translations = {
    "welcome": {
        "en": "Welcome to Smart Farming Flood & Weather Dashboard 🌾",
        "ha": "Barka da zuwa dashboard ɗin noman zamani 🌾",
        "yo": "Kaabo si dasibodu oko ọlọgbọn 🌾",
        "ig": "Nnọọ na dashboard ugbo amamihe 🌾"
    },
    "desc": {
        "en": "Monitor weather and flood indicators for your farming region.",
        "ha": "Bi yanayin sama da alamar ambaliyar ruwa a yankin gonarka.",
        "yo": "Ṣọ oju-ọjọ ati awọn itọkasi ìtànkálẹ omi fun agbegbe rẹ.",
        "ig": "Lelee ihu igwe na ihe ngosi mmiri ozuzo maka mpaghara gị."
    },
    "check_weather": {
        "en": "Check Weather",
        "ha": "Duba Yanayi",
        "yo": "Ṣayẹwo Oju-ọjọ",
        "ig": "Lelee Ihu Igwe"
    },
    "check_flood": {
        "en": "Check Flood",
        "ha": "Duba Ambaliyar Ruwa",
        "yo": "Ṣayẹwo Ìtànkálẹ Omi",
        "ig": "Lelee Mmiri Ozuzo"
    }
}

def t(key, lang="en"):
    if key in translations:
        return translations[key].get(lang, translations[key]["en"])
    return key

# ====== HOME (HTML FRONTEND DASHBOARD) ======
@app.route("/")
def home():
    lang = request.args.get("lang", "en")
    return f"""
    <html>
    <head>
        <title>AgroGuard 🌾</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{
                font-family: 'Segoe UI', sans-serif;
                background: #f4f8f3;
                color: #333;
                text-align: center;
                padding: 30px;
            }}
            h1 {{ color: #2f7a32; }}
            .lang-select {{
                margin: 15px;
            }}
            .card {{
                background: white;
                border-radius: 12px;
                padding: 20px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                margin: 20px auto;
                width: 90%;
                max-width: 450px;
            }}
            button {{
                background-color: #2f7a32;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 8px;
                cursor: pointer;
                font-size: 16px;
            }}
            input {{
                padding: 8px;
                margin: 5px;
                width: 80%;
                border: 1px solid #ccc;
                border-radius: 5px;
            }}
        </style>
    </head>
    <body>
        <h1>{t("welcome", lang)}</h1>
        <p>{t("desc", lang)}</p>

        <div class="lang-select">
            <a href="/?lang=en">English</a> |
            <a href="/?lang=ha">Hausa</a> |
            <a href="/?lang=yo">Yoruba</a> |
            <a href="/?lang=ig">Igbo</a>
        </div>

        <div class="card">
            <h3>🌤️ {t("check_weather", lang)}</h3>
            <input id="lat" placeholder="Latitude" />
            <input id="lon" placeholder="Longitude" />
            <button onclick="checkWeather()">Get Weather</button>
            <pre id="weatherOutput"></pre>
        </div>

        <div class="card">
            <h3>🌊 {t("check_flood", lang)}</h3>
            <input id="flat" placeholder="Latitude" />
            <input id="flon" placeholder="Longitude" />
            <button onclick="checkFlood()">Check Flood</button>
            <pre id="floodOutput"></pre>
        </div>

        <script>
            async function checkWeather() {{
                const lat = document.getElementById('lat').value;
                const lon = document.getElementById('lon').value;
                const res = await fetch(`/weather?lat=${{lat}}&lon=${{lon}}`);
                const data = await res.json();
                document.getElementById('weatherOutput').innerText = JSON.stringify(data, null, 2);
            }}
            async function checkFlood() {{
                const lat = document.getElementById('flat').value;
                const lon = document.getElementById('flon').value;
                const res = await fetch(`/flood_indicator?lat=${{lat}}&lon=${{lon}}`);
                const data = await res.json();
                document.getElementById('floodOutput').innerText = JSON.stringify(data, null, 2);
            }}
        </script>
    </body>
    </html>
    """

# ====== WEATHER & FLOOD API ======
OPENWEATHER_KEY = "YOUR_OPENWEATHER_API_KEY"

@app.route("/weather")
def get_weather():
    lat = request.args.get("lat")
    lon = request.args.get("lon")
    if not lat or not lon:
        return jsonify({"error": "lat/lon required"}), 400
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_KEY}&units=metric"
    res = requests.get(url)
    return jsonify(res.json())

@app.route("/flood_indicator")
def flood_indicator():
    lat = request.args.get("lat")
    lon = request.args.get("lon")
    if not lat or not lon:
        return jsonify({"error": "lat/lon required"}), 400
    # Dummy simulation
    import random
    risk = random.choice(["low", "moderate", "high"])
    return jsonify({"lat": lat, "lon": lon, "flood_risk": risk})

if __name__ == "__main__":
    app.run(debug=True)
    
    states_lgas = [
    {"state":"Abia","lgas":["Aba North","Aba South","Arochukwu","Bende","Ikwuano","Isiala Ngwa North","Isiala Ngwa South","Isuikwuato","Obi Ngwa","Ohafia","Osisioma","Umuahia North","Umuahia South","Umu Nneochi"]},
    {"state":"Adamawa","lgas":["Demsa","Fufure","Ganye","Girei","Gombi","Guyuk","Hong","Jada","Lamurde","Madagali","Maiha","Mayo Belwa","Michika","Mubi North","Mubi South","Numan","Shelleng","Song","Toungo","Yola North","Yola South"]},
    {"state":"Akwa Ibom","lgas":["Abak","Eastern Obolo","Eket","Esit Eket","Essien Udim","Etim Ekpo","Etinan","Ibeno","Ibesikpo Asutan","Ibiono Ibom","Ikono","Ikot Abasi","Ikot Ekpene","Ini","Itu","Mbo","Mkpat Enin","Nsit Atai","Nsit Ibom","Nsit Ubium","Obot Akara","Okobo","Onna","Oron","Oruk Anam","Udung Uko","Ukanafun","Uruan","Urue-Offong/Oruko","Uyo"]},
    {"state":"Anambra","lgas":["Aguata","Anambra East","Anambra West","Anaocha","Awka North","Awka South","Ayamelum","Dunukofia","Ekwusigo","Idemili North","Idemili South","Ihiala","Njikoka","Nnewi North","Nnewi South","Ogbaru","Onitsha North","Onitsha South","Orumba North","Orumba South","Oyi"]},
    {"state":"Bauchi","lgas":["Bauchi","Bogoro","Damban","Darazo","Dass","Gamawa","Ganjuwa","Giade","Itas/Gadau","Jama’are","Katagum","Kirfi","Misau","Ningi","Shira","Tafawa Balewa","Toro","Warji","Zaki"]},
    {"state":"Bayelsa","lgas":["Brass","Ekeremor","Kolokuma/Opokuma","Nembe","Ogbia","Sagbama","Southern Ijaw","Yenagoa"]},
    {"state":"Benue","lgas":["Ado","Agatu","Apa","Buruku","Gboko","Guma","Gwer East","Gwer West","Katsina-Ala","Konshisha","Kwande","Logo","Makurdi","Obi","Ogbadibo","Ohimini","Oju","Okpokwu","Otukpo","Tarka","Ukum","Vandeikya"]},
    {"state":"Borno","lgas":["Abadam","Askira/Uba","Bama","Bayo","Biu","Chibok","Damboa","Dikwa","Gubio","Guzamala","Gwoza","Hawul","Jere","Kaga","Kala/Balge","Konduga","Kukawa","Kwaya Kusar","Mafa","Magumeri","Maiduguri","Marte","Mobbar","Monguno","Ngala","Nganzai","Shani"]},
    {"state":"Cross River","lgas":["Akpabuyo","Odukpani","Akamkpa","Biase","Abi","Ikom","Obanliku","Obubra","Obudu","Ogoja","Yala","Bekwara","Bakassi","Calabar Municipal","Calabar South","Etung","Boki","Tarkwa Bay"]},
    {"state":"Delta","lgas":["Oshimili North","Oshimili South","Aniocha North","Aniocha South","Ika North East","Ika South","Ndokwa East","Ndokwa West","Isoko North","Isoko South","Okpe","Oshimili South","Sapele","Udu","Ughelli North","Ughelli South","Uvwie","Warri North","Warri South","Warri South West"]},
    {"state":"Ebonyi","lgas":["Abakaliki","Afikpo North","Afikpo South","Ebonyi","Ezza North","Ezza South","Ikwo","Ishielu","Ivo","Izzi","Ohaozara","Ohaukwu","Onicha"]},
    {"state":"Edo","lgas":["Akoko-Edo","Egor","Esan Central","Esan North-East","Esan South-East","Esan West","Etsako Central","Etsako East","Etsako West","Igueben","Ikpoba-Okha","Oredo","Orhionmwon","Ovia North-East","Ovia South-West","Owan East","Owan West","Uhunmwonde"]},
    {"state":"Ekiti","lgas":["Ado","Efon","Ekiti East","Ekiti South-West","Ekiti West","Emure","Gbonyin","Ido-Osi","Ijero","Ikere","Ikole","Ilejemeje","Irepodun/Ifelodun","Ise/Orun","Moba","Oye"]},
    {"state":"Enugu","lgas":["Enugu East","Enugu North","Enugu South","Ezeagu","Igbo Etiti","Igbo Eze North","Igbo Eze South","Isi Uzo","Nkanu East","Nkanu West","Nsukka","Oji River","Udenu","Udi","Uzo Uwani"]},
    {"state":"Gombe","lgas":["Akko","Balanga","Billiri","Dukku","Funakaye","Gombe","Kaltungo","Kwami","Nafada/Bajoga","Shongom","Yamaltu/Deba"]},
    {"state":"Imo","lgas":["Aboh Mbaise","Ahiazu Mbaise","Ehime Mbano","Ezinihitte","Ideato North","Ideato South","Ihitte/Uboma","Ikeduru","Isiala Mbano","Isu","Mbaitoli","Ngor Okpala","Njaba","Nkwerre","Nwangele","Obowo","Oguta","Ohaji/Egbema","Okigwe","Orlu","Orsu","Oru East","Oru West","Owerri Municipal","Owerri North","Owerri West"]},
    {"state":"Jigawa","lgas":["Auyo","Babura","Biriniwa","Birnin Kudu","Buji","Dutse","Gagarawa","Garki","Gumel","Guri","Gwaram","Gwiwa","Hadejia","Jahun","Kafin Hausa","Kaugama","Kazaure","Kiri Kasama","Kiyawa","Maigatari","Malam Madori","Miga","Ringim","Roni","Sule Tankarkar","Taura","Yankwashi"]},
    {"state":"Kaduna","lgas":["Birnin Gwari","Chikun","Giwa","Igabi","Ikara","Jaba","Jema’a","Kachia","Kaduna North","Kaduna South","Kagarko","Kajuru","Kaura","Kauru","Kubau","Kudan","Lere","Makarfi","Sabon Gari","Sanga","Soba","Zangon Kataf","Zaria"]},
    {"state":"Kano","lgas":["Ajingi","Albasu","Bagwai","Bebeji","Bichi","Bunkure","Dala","Dambatta","Dawakin Kudu","Dawakin Tofa","Doguwa","Fagge","Gabasawa","Garko","Garun Mallam","Gaya","Gezawa","Gwale","Gwarzo","Kabo","Kano Municipal","Karaye","Kibiya","Kiru","Kumbotso","Kunchi","Kura","Madobi","Makoda","Minjibir","Nasarawa","Rano","Rimin Gado","Rogo","Shanono","Sumaila","Takai","Tarauni","Tofa","Tsanyawa","Tudun Wada","Ungogo","Warawa","Wudil"]},
    {"state":"Katsina","lgas":["Bakori","Batagarawa","Batsari","Baure","Bindawa","Charanchi","Dandume","Danja","Dan Musa","Daura","Dutsi","Dutsin Ma","Faskari","Funtua","Ingawa","Jibia","Kafur","Kaita","Kankara","Kankia","Katsina","Kurfi","Kusada","Mai’Adua","Malumfashi","Mani","Mashi","Matazu","Musawa","Rimi","Sabuwa","Safana","Sandamu","Zango"]},
    {"state":"Kebbi","lgas":["Aleiro","Arewa Dandi","Argungu","Augie","Bagudo","Birnin Kebbi","Bunza","Dandi","Fakai","Gwandu","Jega","Kalgo","Koko/Besse","Maiyama","Ngaski","Sakaba","Shanga","Suru","Wasagu/Danko","Yauri","Zuru"]},
    {"state":"Kogi","lgas":["Adavi","Ajaokuta","Ankpa","Bassa","Dekina","Ibaji","Idah","Ijumu","Kabba/Bunu","Kogi","Lokoja","Mopa-Muro","Ofu","Ogori/Magongo","Okehi","Okene","Olamaboro","Omala","Yagba East","Yagba West"]},
    {"state":"Kwara","lgas":["Asa","Baruten","Edu","Ekiti","Ifelodun","Ilorin East","Ilorin South","Ilorin West","Irepodun","Isin","Kaiama","Moro","Offa","Oke Ero","Oyun","Pategi"]},
    {"state":"Lagos","lgas":["Agege","Ajeromi-Ifelodun","Alimosho","Amuwo-Odofin","Apapa","Badagry","Epe","Eti-Osa","Ibeju-Lekki","Ifako-Ijaiye","Ikeja","Ikorodu","Kosofe","Lagos Island","Lagos Mainland","Mushin","Ojo","Oshodi-Isolo","Shomolu","Surulere"]},
    {"state":"Nasarawa","lgas":["Akwanga","Awe","Doma","Karu","Keana","Keffi","Kokona","Lafia","Nasarawa","Nasarawa Egon","Obi","Toto","Wamba"]},
    {"state":"Niger","lgas":["Agaie","Agwara","Bida","Borgu","Bosso","Chanchaga","Edati","Gbako","Gurara","Katcha","Kontagora","Lapai","Lavun","Magama","Mariga","Mashegu","Mokwa","Muya","Paikoro","Rafi","Rijau","Shiroro","Suleja","Tafa","Wushishi"]},
    {"state":"Ogun","lgas":["Abeokuta North","Abeokuta South","Ado-Odo/Ota","Egbado North","Egbado South","Ewekoro","Ifo","Ijebu East","Ijebu North","Ijebu North East","Ijebu Ode","Ikenne","Imeko Afon","Ipokia","Obafemi-Owode","Odogbolu","Ogun Waterside","Remo North","Shagamu"]},
    {"state":"Ondo","lgas":["Akoko North-East","Akoko North-West","Akoko South-East","Akoko South-West","Akure North","Akure South","Ese Odo","Idanre","Ifedore","Ilaje","Ile Oluji/Okeigbo","Irele","Odigbo","Okitipupa","Ondo East","Ondo West","Ose","Owo"]},
    {"state":"Osun","lgas":["Aiyedaade","Aiyedire","Atakumosa East","Atakumosa West","Boluwaduro","Boripe","Ede North","Ede South","Egbedore","Ejigbo","Ife Central","Ife East","Ife North","Ife South","Ifedayo","Ifelodun","Ila","Ilesa East","Ilesa West","Irepodun","Irewole","Isokan","Iwo","Obokun","Odo Otin","Ola Oluwa","Olorunda","Oriade","Orolu","Osogbo"]},
    {"state":"Oyo","lgas":["Afijio","Akinyele","Atiba","Atisbo","Egbeda","Ibadan North","Ibadan North-East","Ibadan North-West","Ibadan South-East","Ibadan South-West","Ibarapa Central","Ibarapa East","Ibarapa North","Ido","Irepo","Iseyin","Itesiwaju","Iwajowa","Kajola","Lagelu","Ogbomosho North","Ogbomosho South","Ogo Oluwa","Olorunsogo","Oluyole","Ona Ara","Orelope","Ori Ire","Oyo","Oyo East","Saki East","Saki West","Surulere"]},
    {"state":"Plateau","lgas":["Barkin Ladi","Bassa","Bokkos","Jos East","Jos North","Jos South","Kanam","Kanke","Langtang North","Langtang South","Mangu","Mikang","Pankshin","Qua’an Pan","Riyom","Shendam","Wase"]},
    {"state":"Rivers","lgas":["Abua/Odual","Ahoada East","Ahoada West","Akuku-Toru","Andoni","Asari-Toru","Bonny","Degema","Eleme","Emohua","Etche","Gokana","Ikwerre","Khana","Obio/Akpor","Ogba/Egbema/Ndoni","Ogu/Bolo","Okrika","Omuma","Opobo/Nkoro","Oyigbo","Port Harcourt","Tai"]},
    {"state":"Sokoto","lgas":["Binji","Bodinga","Dange Shuni","Gada","Goronyo","Gudu","Gwadabawa","Illela","Isa","Kebbe","Kware","Rabah","Sabon Birni","Shagari","Silame","Sokoto North","Sokoto South","Tambuwal","Tangaza","Tureta","Wamako","Wurno","Yabo"]},
    {"state":"Taraba","lgas":["Ardo Kola","Bali","Donga","Gashaka","Gassol","Ibi","Jalingo","Karim Lamido","Kumi","Lau","Sardauna","Takum","Ussa","Wukari","Yorro","Zing"]},
    {"state":"Yobe","lgas":["Bade","Bursari","Damaturu","Fika","Fune","Geidam","Gujba","Gulani","Jakusko","Karasuwa","Machina","Nangere","Nguru","Potiskum","Tarmuwa","Yunusari","Yusufari"]},
    {"state":"Zamfara","lgas":["Anka","Bakura","Birnin Magaji/Kiyaw","Bukkuyum","Bungudu","Gummi","Gusau","Kaura Namoda","Maradun","Maru","Shinkafi","Talata Mafara","Chafe","Zurmi"]}
]
