from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3, requests, hashlib, time

app = Flask(__name__)
CORS(app)
# =============== MULTI-LANGUAGE TRANSLATION SUPPORT ==================

# Dictionary da ke ɗauke da fassarar sakonni a harsuna 4
translations = {
    "welcome": {
        "en": "Welcome to Smart Farming Flood & Weather Guide API",
        "ha": "Barka da zuwa tsarin noman zamani da ke taimaka wajen lura da ambaliyar ruwa da yanayi",
        "yo": "Kaabo si eto oko ọlọgbọn fun ìtànkálẹ omi ati oju-ọjọ",
        "ig": "Nnọọ na usoro ugbo amamihe maka mmiri na ihu igwe"
    },
    "register_success": {
        "en": "User registered successfully!",
        "ha": "An yi rajistar mai amfani cikin nasara!",
        "yo": "A ti forukọsilẹ olumulo ni aṣeyọri!",
        "ig": "A debanyere onye ọrụ nke ọma!"
    },
    "login_success": {
        "en": "Login successful",
        "ha": "Shiga cikin nasara",
        "yo": "Wọle ni aṣeyọri",
        "ig": "Ịbanye gara nke ọma"
    },
    "invalid_credentials": {
        "en": "Invalid email or password",
        "ha": "Imel ko kalmar sirri ba daidai ba ce",
        "yo": "Imeeli tabi ọrọ igbaniwọle ti ko tọ",
        "ig": "Email ma ọ bụ paswọọdụ ezighi ezi"
    },
    "farm_added": {
        "en": "Farm added successfully!",
        "ha": "An ƙara gona cikin nasara!",
        "yo": "Oko ti fi kun ni aṣeyọri!",
        "ig": "A tinyere ugbo nke ọma!"
    },
    "weather_loaded": {
        "en": "Weather data loaded successfully.",
        "ha": "An loda bayanan yanayi cikin nasara.",
        "yo": "A ti gba data oju-ọjọ ni aṣeyọri.",
        "ig": "E zigara data ihu igwe nke ọma."
    },
    "flood_warning": {
        "en": "Flood risk detected in your area!",
        "ha": "An gano haɗarin ambaliyar ruwa a yankinka!",
        "yo": "E ri ewu ìtànkálẹ omi ni agbegbe rẹ!",
        "ig": "Achọpụtala ihe egwu mmiri ozuzo na mpaghara gị!"
    }
}

# Wannan function ɗin tana karɓar sakon da harshen da ake so, ta dawo da fassarar
def t(key, lang="en"):
    """Return translation text based on selected language."""
    if key in translations:
        return translations[key].get(lang, translations[key]["en"])
    return key

DB_NAME = "farming.db"

# =============== DATABASE SETUP ==================
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            password_hash TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS farms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT,
            crop_type TEXT,
            lat REAL,
            lon REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS flood_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT,
            description TEXT,
            severity TEXT,
            lat REAL,
            lon REAL,
            event_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

init_db()

# =============== HELPERS ==================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def query_db(query, args=(), one=False):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cur = conn.execute(query, args)
    rv = cur.fetchall()
    conn.commit()
    conn.close()
    return (rv[0] if rv else None) if one else rv

# =============== AUTH ROUTES ==================
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    name, email, password = data.get("name"), data.get("email"), data.get("password")
    if not all([name, email, password]):
        return jsonify({"error": "Missing fields"}), 400
    try:
        query_db("INSERT INTO users (name,email,password_hash) VALUES (?,?,?)",
                 (name, email, hash_password(password)))
        return jsonify({"message": "User registered successfully!"})
    except sqlite3.IntegrityError:
        return jsonify({"error": "Email already registered"}), 400

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email, password = data.get("email"), data.get("password")
    user = query_db("SELECT * FROM users WHERE email=? AND password_hash=?",
                    (email, hash_password(password)), one=True)
    if user:
        return jsonify({"message": "Login successful", "user_id": user["id"], "name": user["name"]})
    else:
        return jsonify({"error": "Invalid credentials"}), 401

# =============== FARM ROUTES ==================
@app.route("/add_farm", methods=["POST"])
def add_farm():
    data = request.get_json()
    user_id = data.get("user_id")
    name = data.get("name")
    crop_type = data.get("crop_type")
    lat = data.get("lat")
    lon = data.get("lon")

    if not all([user_id, name, lat, lon]):
        return jsonify({"error": "Missing fields"}), 400

    query_db("INSERT INTO farms (user_id,name,crop_type,lat,lon) VALUES (?,?,?,?,?)",
             (user_id, name, crop_type, lat, lon))
    return jsonify({"message": "Farm added successfully!"})

@app.route("/get_farms/<int:user_id>")
def get_farms(user_id):
    farms = query_db("SELECT * FROM farms WHERE user_id=?", (user_id,))
    return jsonify([dict(f) for f in farms])

# =============== WEATHER & FLOOD ROUTES ==================
OPENWEATHER_KEY = "YOUR_OPENWEATHER_API_KEY"  # register free at openweathermap.org
OPEN_METEO_URL = "https://api.open-meteo.com/v1/flood"

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

    try:
        response = requests.get(f"{OPEN_METEO_URL}?latitude={lat}&longitude={lon}")
        data = response.json()
        discharge = data.get("discharge")
        risk = "low"
        if discharge:
            avg_discharge = sum(discharge) / len(discharge)
            if avg_discharge > 5000:
                risk = "high"
            elif avg_discharge > 2000:
                risk = "moderate"
        return jsonify({"risk": risk, "avg_discharge": discharge})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/get_floods")
def get_floods():
    floods = query_db("SELECT * FROM flood_events ORDER BY event_time DESC LIMIT 10")
    return jsonify([dict(f) for f in floods])

# =============== HOME ==================
@app.route("/")
def home():
    return jsonify({
        "message": "Welcome to Smart Farming Flood & Weather Guide API",
        "routes": ["/register", "/login", "/add_farm", "/get_farms/<user_id>", "/weather?lat=&lon=", "/flood_indicator?lat=&lon="]
    })

# =============== RUN APP ==================
if __name__ == "__main__":
    print("🚜 Running server on http://127.0.0.1:5000")
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
