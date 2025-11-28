from flask import Flask, render_template_string, request, jsonify
import math
import random
import requests
from typing import Optional

app = Flask(__name__)

# --- CONFIGURATION & DATA ---

# Carbon Pricing (Simulated)
CARBON_PRICE_DEFAULT = 50.0 

# Carbon Intensity (gCO2/kWh) - Comprehensive List
CARBON_INTENSITY = {
    "US": 424, "IN": 705, "DE": 369, "FR": 57, "BR": 89,
    "CA": 130, "AU": 680, "JP": 480, "GB": 230, "IT": 300,
    "MX": 380, "ZA": 850, "KR": 450, "ES": 200, "SE": 15,
    "CN": 580, "RU": 470, "AR": 360, "EG": 450, "NG": 400,
    "NO": 8, "IS": 0, "NZ": 120, "CH": 30, "FI": 90,
    "DK": 150, "NL": 390, "BE": 220, "AT": 140, "PL": 690
}

# Currency Symbols
CURRENCY_SYMBOL = {
    "US": "$", "IN": "₹", "DE": "€", "FR": "€", "BR": "R$",
    "CA": "$", "AU": "$", "JP": "¥", "GB": "£", "IT": "€",
    "MX": "$", "ZA": "R", "KR": "₩", "ES": "€", "SE": "kr",
    "CN": "¥", "RU": "₽", "AR": "$", "EG": "E£", "NG": "₦",
    "NO": "kr", "IS": "kr", "NZ": "$", "CH": "Fr", "FI": "€",
    "DK": "kr", "NL": "€", "BE": "€", "AT": "€", "PL": "zł"
}

# Electricity Rates (Approximate per kWh in local currency)
ELECTRICITY_RATE = {
    "US": 0.14, "IN": 7.0, "DE": 0.36, "FR": 0.19, "BR": 0.80,
    "CA": 0.13, "AU": 0.35, "JP": 27.0, "GB": 0.34, "IT": 0.28,
    "MX": 2.0, "ZA": 2.5, "KR": 120, "ES": 0.25, "SE": 2.5,
    "CN": 0.6, "RU": 5.0, "AR": 50.0, "EG": 1.5, "NG": 50.0,
    "NO": 1.5, "IS": 18.0, "NZ": 0.30, "CH": 0.25, "FI": 0.17,
    "DK": 2.5, "NL": 0.30, "BE": 0.30, "AT": 0.25, "PL": 0.70
}

# Renewable Potential Database
RENEWABLE_POTENTIAL = {
    "US": {"solar": "excellent", "wind": "good", "hydro": "moderate"},
    "IN": {"solar": "excellent", "wind": "moderate", "hydro": "good"},
    "DE": {"solar": "moderate", "wind": "excellent", "hydro": "low"},
    "FR": {"solar": "good", "wind": "good", "hydro": "excellent"},
    "BR": {"solar": "excellent", "wind": "good", "hydro": "excellent"},
    "CA": {"solar": "moderate", "wind": "excellent", "hydro": "excellent"},
    "AU": {"solar": "excellent", "wind": "excellent", "hydro": "low"},
    "JP": {"solar": "good", "wind": "moderate", "hydro": "good"},
    "GB": {"solar": "low", "wind": "excellent", "hydro": "moderate"},
    "SE": {"solar": "low", "wind": "good", "hydro": "excellent"}
}

# Energy Saving Tips Database
ENERGY_TIPS = {
    "ac": [
        "🌡️ Set AC to 24-26°C. Each degree lower increases energy use by 6-8%.",
        "🪟 Use ceiling fans with AC to feel 4°C cooler at the same temperature.",
        "🌙 Use programmable thermostats/timers for night cooling."
    ],
    "heating": [
        "🔥 Lower thermostat by 1°C to save 10% on heating bills.",
        "🏠 Seal windows and doors to prevent 20% heat loss.",
        "☀️ Open curtains during sunny days for free solar heating."
    ],
    "office": [
        "💻 Use laptop instead of desktop - uses 50-80% less power.",
        "🔌 Use smart power strips to eliminate phantom loads from peripherals."
    ],
    "ev": [
        "🚗 Charge during off-peak hours (usually 10 PM - 6 AM).",
        "🔋 Maintain battery between 20-80% for longevity."
    ],
    "appliances": [
        "🧺 Wash clothes in cold water - saves 90% of washing energy.",
        "❄️ Keep fridge at 3-5°C and freezer at -18°C."
    ],
    "lighting": [
        "💡 Switch to LED bulbs - use 75% less energy, last 25x longer.",
        "🌅 Use natural daylight and light-colored walls."
    ]
}

# India Data
INDIA_STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand",
    "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur",
    "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
    "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
    "Uttar Pradesh", "Uttarakhand", "West Bengal"
]

CITIES_BY_STATE = {
    "Karnataka": ["Bengaluru", "Mysore", "Hubli", "Mangalore", "Bidar", "Belgaum"],
    "Maharashtra": ["Mumbai", "Pune", "Nagpur", "Nashik", "Aurangabad"],
    "Delhi": ["New Delhi", "North Delhi", "South Delhi"],
    "Tamil Nadu": ["Chennai", "Coimbatore", "Madurai", "Salem"],
    "Uttar Pradesh": ["Lucknow", "Kanpur", "Varanasi", "Agra", "Noida"],
    "Telangana": ["Hyderabad", "Warangal", "Nizamabad"],
    "Gujarat": ["Ahmedabad", "Surat", "Vadodara", "Rajkot"],
    "West Bengal": ["Kolkata", "Howrah", "Durgapur"],
    "Rajasthan": ["Jaipur", "Jodhpur", "Udaipur", "Kota"]
}

BIDAR_TOWNS = ["Aurad", "Basavakalyan", "Bhalki", "Chitgoppa", "Hulsoor", "Humnabad", 
               "Kamalnagar", "Old City", "New City", "Gumpa", "Mailoor", "Chidri"]

# Examples
EXAMPLES = [
    {"name": "Urban Apt (US)", "location": "US", "usage": 12, "habits": "AC in summer, WFH setup", "icon": "🏢"},
    {"name": "Family Home (IN)", "location": "IN", "usage": 16, "habits": "Fans, Lights, TV, Fridge", "icon": "🏠"},
    {"name": "Eco Student (DE)", "location": "DE", "usage": 6, "habits": "Laptop, LED lights, No AC", "icon": "📚"}
]

# --- HELPER FUNCTIONS ---

def get_current_weather(location: str) -> Optional[dict]:
    coord_map = {
        "US": (37.09, -95.71), "IN": (20.59, 78.96), "DE": (51.16, 10.45),
        "FR": (46.22, 2.21), "BR": (-14.23, -51.92), "CA": (56.13, -106.34),
        "AU": (-25.27, 133.77), "JP": (36.20, 138.25), "GB": (55.37, -3.43),
        "IT": (41.87, 12.56)
    }
    lat, lon = coord_map.get(location, (0, 0))
    if lat == 0: return None

    try:
        params = {"latitude": lat, "longitude": lon, "current": "temperature_2m,weather_code,relative_humidity_2m"}
        r = requests.get("https://api.open-meteo.com/v1/forecast", params=params, timeout=3)
        if r.status_code == 200:
            data = r.json()['current']
            desc_map = {0: "Clear Sky", 1: "Mainly Clear", 2: "Partly Cloudy", 3: "Overcast", 45: "Foggy", 61: "Rain", 80: "Showers"}
            return {
                "temperature": data['temperature_2m'],
                "humidity": data['relative_humidity_2m'],
                "description": desc_map.get(data['weather_code'], "Variable"),
                "feels_like": data['temperature_2m']
            }
    except:
        return None
    return None

# --- HTML TEMPLATE ---

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Eco-Genius | Smart Energy Planning</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <script src="https://unpkg.com/gsap@3.12.5/dist/gsap.min.js"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
    body { font-family: 'Inter', sans-serif; background: #050510; color: #e2e8f0; overflow-x: hidden; }
    
    .gradient-bg {
      position: fixed; top: 0; left: 0; right: 0; bottom: 0;
      background: linear-gradient(125deg, #0a0f1c 0%, #0f1729 25%, #0a1628 50%, #051119 75%, #0a0f1c 100%);
      background-size: 400% 400%; animation: gradientShift 20s ease infinite; z-index: -2;
    }
    @keyframes gradientShift { 0%, 100% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } }
    
    .particles { position: fixed; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; z-index: -1; }
    .particle { position: absolute; width: 2px; height: 2px; background: rgba(52, 211, 153, 0.4); border-radius: 50%; animation: float 20s infinite linear; }
    
    .glass-card {
      background: rgba(15, 23, 42, 0.7); backdrop-filter: blur(16px);
      border: 1px solid rgba(71, 85, 105, 0.4); border-radius: 24px;
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5); transition: all 0.3s ease;
    }
    .glass-card:hover { transform: translateY(-5px); border-color: rgba(52, 211, 153, 0.5); }

    .glow-button {
      background: linear-gradient(135deg, #10b981 0%, #0d9488 100%);
      border-radius: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;
      transition: all 0.3s ease;
    }
    .glow-button:hover { transform: scale(1.02); box-shadow: 0 0 20px rgba(52, 211, 153, 0.5); }

    #map { height: 300px; border-radius: 16px; width: 100%; z-index: 0; }
    select, input, textarea { background: rgba(30, 41, 59, 0.6); border: 1px solid rgba(71, 85, 105, 0.5); color: white; }
  </style>
</head>
<body>
  <div class="gradient-bg"></div>
  <div class="particles" id="particles"></div>
  
  <div class="container mx-auto px-4 py-8 max-w-6xl relative z-10">
    
    <header class="text-center mb-12">
      <h1 class="text-5xl md:text-6xl font-black mb-4">
        <span class="bg-clip-text text-transparent bg-gradient-to-r from-emerald-400 via-teal-500 to-cyan-500">
          Eco-Genius
        </span>
      </h1>
      <p class="text-xl text-slate-300">AI-Powered Energy Planning & Carbon Optimization</p>
    </header>

    <section class="mb-10">
      <h2 class="text-2xl font-bold text-white mb-6">Quick Start Templates</h2>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        {% for ex in examples %}
        <div class="glass-card p-6 cursor-pointer" onclick="loadExample('{{ ex.location }}', {{ ex.usage }}, `{{ ex.habits }}`)">
          <div class="flex justify-between items-center mb-3">
            <span class="text-3xl">{{ ex.icon }}</span>
            <span class="text-xs bg-slate-700 px-2 py-1 rounded text-slate-300">{{ ex.location }}</span>
          </div>
          <h3 class="font-bold text-white">{{ ex.name }}</h3>
          <p class="text-sm text-slate-400 mt-2">{{ ex.habits }}</p>
        </div>
        {% endfor %}
      </div>
    </section>

    <div class="glass-card p-8 mb-12" id="inputCard">
      <div class="flex items-center gap-4 mb-8">
        <div class="w-10 h-10 rounded-full bg-emerald-500 flex items-center justify-center">
          <i class="fas fa-sliders-h text-white"></i>
        </div>
        <h2 class="text-2xl font-bold text-white">Analysis Parameters</h2>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        <div class="space-y-6">
          
          <div>
            <label class="block text-sm font-medium text-emerald-400 mb-2">Location</label>
            <select id="location" class="w-full p-3 rounded-xl focus:outline-none focus:border-emerald-500" onchange="handleLocationChange()">
              <option value="US">🇺🇸 United States</option>
              <option value="IN">🇮🇳 India</option>
              <option value="DE">🇩🇪 Germany</option>
              <option value="FR">🇫🇷 France</option>
              <option value="BR">🇧🇷 Brazil</option>
              <option value="CA">🇨🇦 Canada</option>
              <option value="AU">🇦🇺 Australia</option>
              <option value="JP">🇯🇵 Japan</option>
              <option value="GB">🇬🇧 United Kingdom</option>
            </select>
          </div>

          <div id="india-fields" class="hidden space-y-4 border-l-2 border-emerald-500 pl-4 bg-slate-800/30 p-4 rounded-r-xl">
            <div>
              <label class="block text-xs text-slate-400 mb-1">State</label>
              <select id="state" class="w-full p-2 rounded-lg text-sm" onchange="handleStateChange()">
                <option value="">Select State</option>
                {% for state in india_states %}
                <option value="{{ state }}">{{ state }}</option>
                {% endfor %}
              </select>
            </div>
            
            <div id="city-wrapper" class="hidden">
              <label class="block text-xs text-slate-400 mb-1">City</label>
              <select id="city" class="w-full p-2 rounded-lg text-sm" onchange="handleCityChange()">
                <option value="">Select City</option>
              </select>
            </div>

            <div id="town-wrapper" class="hidden">
              <label class="block text-xs text-slate-400 mb-1">Town (Bidar District)</label>
              <select id="town" class="w-full p-2 rounded-lg text-sm">
                <option value="">Select Town</option>
                {% for town in bidar_towns %}
                <option value="{{ town }}">{{ town }}</option>
                {% endfor %}
              </select>
            </div>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-emerald-400 mb-2">Daily Usage (Hours)</label>
              <input type="number" id="daily_hours" value="12" class="w-full p-3 rounded-xl focus:border-emerald-500" placeholder="e.g. 12">
            </div>
            <div>
              <label class="block text-sm font-medium text-emerald-400 mb-2">Est. Load Type</label>
              <div class="text-xs text-slate-400 mt-2 italic" id="load-preview">Auto-calculated based on habits</div>
            </div>
          </div>

          <div>
            <label class="block text-sm font-medium text-emerald-400 mb-2">Energy Habits</label>
            <textarea id="habits" class="w-full p-3 rounded-xl h-24 focus:border-emerald-500" 
                      placeholder="Describe appliances: 'I run AC for 8 hours, have an EV car, work from home on laptop...'"></textarea>
          </div>

          <button onclick="analyze()" class="glow-button w-full py-4 text-white shadow-lg">
            Generate Eco-Plan <i class="fas fa-arrow-right ml-2"></i>
          </button>
        </div>

        <div class="space-y-6">
           <label class="block text-sm font-medium text-emerald-400">Regional Context</label>
           <div id="map"></div>
           
           <div class="grid grid-cols-2 gap-4">
             <div id="weatherDisplay" class="glass-card p-4 hidden">
               <div class="flex items-center gap-3">
                 <i class="fas fa-cloud-sun text-yellow-400 text-2xl"></i>
                 <div>
                   <p class="text-lg font-bold text-white" id="tempDisplay">--</p>
                   <p class="text-xs text-slate-400" id="weatherDesc">--</p>
                 </div>
               </div>
             </div>
             
             <div class="glass-card p-4">
               <div class="flex items-center gap-3">
                 <i class="fas fa-dollar-sign text-green-400 text-2xl"></i>
                 <div>
                   <p class="text-lg font-bold text-white" id="carbonPriceDisplay">Loading...</p>
                   <p class="text-xs text-slate-400">Current Carbon Price</p>
                 </div>
               </div>
             </div>
           </div>
        </div>
      </div>
    </div>

    <section id="results" class="hidden space-y-8">
      
      <div class="glass-card p-8">
        <div class="flex justify-between items-start border-b border-slate-700 pb-4 mb-6">
            <h3 class="text-2xl font-bold text-white">Analysis Results</h3>
            <div id="profile-tags" class="flex gap-2 flex-wrap justify-end"></div>
        </div>
        
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6 text-center">
          <div class="p-4 bg-slate-800/40 rounded-xl">
            <p class="text-slate-400 text-xs uppercase tracking-wider">Carbon Footprint</p>
            <p class="text-3xl font-black text-white mt-2"><span id="res-carbon" class="text-red-400">0</span> kg</p>
          </div>
          <div class="p-4 bg-slate-800/40 rounded-xl">
            <p class="text-slate-400 text-xs uppercase tracking-wider">Trees to Offset</p>
            <p class="text-3xl font-black text-white mt-2"><span id="res-trees" class="text-emerald-400">0</span> 🌳</p>
          </div>
          <div class="p-4 bg-slate-800/40 rounded-xl">
            <p class="text-slate-400 text-xs uppercase tracking-wider">Potential Savings</p>
            <p class="text-3xl font-black text-white mt-2"><span id="res-savings" class="text-yellow-400">0</span></p>
          </div>
          <div class="p-4 bg-slate-800/40 rounded-xl">
            <p class="text-slate-400 text-xs uppercase tracking-wider">Payback Period</p>
            <p class="text-3xl font-black text-white mt-2"><span id="res-payback" class="text-blue-400">0</span> yrs</p>
          </div>
        </div>
        <p class="text-center text-slate-400 mt-4 italic" id="habits-summary"></p>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div class="glass-card p-6">
          <h4 class="text-xl font-bold text-emerald-400 mb-4"><i class="fas fa-check-circle mr-2"></i>Tailored Action Plan</h4>
          <ul id="action-list" class="space-y-3 text-slate-300"></ul>
        </div>
        <div class="glass-card p-6">
          <h4 class="text-xl font-bold text-cyan-400 mb-4"><i class="fas fa-wind mr-2"></i>Renewable Strategy</h4>
          <ul id="renewable-list" class="space-y-3 text-slate-300"></ul>
        </div>
      </div>
      
      <div class="glass-card p-6">
        <h4 class="text-xl font-bold text-yellow-400 mb-4"><i class="fas fa-lightbulb mr-2"></i>Smart Efficiency Tips</h4>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4" id="tips-grid"></div>
      </div>

    </section>

    <section class="mt-12">
      <h2 class="text-2xl font-bold text-white mb-6">Investment Estimators</h2>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        <div class="glass-card p-6 border-t-4 border-yellow-500">
          <h3 class="font-bold text-white text-lg mb-4 flex items-center"><i class="fas fa-sun text-yellow-500 mr-2"></i> Solar Calculator</h3>
          <div class="space-y-3">
             <input type="number" id="solarRoof" placeholder="Roof Size (sq ft)" value="500" class="w-full p-2 rounded text-sm">
             <button onclick="calcSolar()" class="w-full py-2 bg-yellow-600/20 text-yellow-400 border border-yellow-500/50 rounded hover:bg-yellow-600/40 transition">Calculate</button>
             <div id="solar-res" class="hidden mt-3 text-sm text-slate-300">
                <p>Cost: <b id="solar-cost" class="text-white"></b></p>
                <p>Savings: <b id="solar-save" class="text-white"></b>/yr</p>
             </div>
          </div>
        </div>

        <div class="glass-card p-6 border-t-4 border-blue-500">
          <h3 class="font-bold text-white text-lg mb-4 flex items-center"><i class="fas fa-fan text-blue-500 mr-2"></i> Wind Calculator</h3>
          <div class="space-y-3">
             <input type="number" id="windSize" placeholder="Turbine Size (kW)" value="5" class="w-full p-2 rounded text-sm">
             <button onclick="calcWind()" class="w-full py-2 bg-blue-600/20 text-blue-400 border border-blue-500/50 rounded hover:bg-blue-600/40 transition">Calculate</button>
             <div id="wind-res" class="hidden mt-3 text-sm text-slate-300">
                <p>Cost: <b id="wind-cost" class="text-white"></b></p>
                <p>Energy: <b id="wind-kwh" class="text-white"></b> kWh/yr</p>
             </div>
          </div>
        </div>

        <div class="glass-card p-6 border-t-4 border-cyan-500">
          <h3 class="font-bold text-white text-lg mb-4 flex items-center"><i class="fas fa-water text-cyan-500 mr-2"></i> Hydro Calculator</h3>
          <div class="space-y-3">
             <div class="flex gap-2">
               <input type="number" id="hydroFlow" placeholder="Flow (L/s)" value="20" class="w-full p-2 rounded text-sm">
               <input type="number" id="hydroHead" placeholder="Head (m)" value="5" class="w-full p-2 rounded text-sm">
             </div>
             <button onclick="calcHydro()" class="w-full py-2 bg-cyan-600/20 text-cyan-400 border border-cyan-500/50 rounded hover:bg-cyan-600/40 transition">Calculate</button>
             <div id="hydro-res" class="hidden mt-3 text-sm text-slate-300">
                <p>Cost: <b id="hydro-cost" class="text-white"></b></p>
                <p>Size: <b id="hydro-size" class="text-white"></b> kW</p>
             </div>
          </div>
        </div>

      </div>
    </section>

  </div>

  <script>
    // --- PARTICLE EFFECT ---
    const pContainer = document.getElementById('particles');
    for(let i=0; i<40; i++){
      const p = document.createElement('div');
      p.className = 'particle';
      p.style.left = Math.random()*100 + '%';
      p.style.animationDelay = Math.random()*20 + 's';
      pContainer.appendChild(p);
    }

    // --- DATA ---
    const citiesByState = {{ cities_by_state | tojson }};

    // --- MAP LOGIC ---
    let map;
    function initMap() {
      map = L.map('map').setView([20, 0], 1);
      L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; OpenStreetMap &copy; CARTO'
      }).addTo(map);

      // Markers
      const coords = {
        "US": [37.09, -95.71], "IN": [20.59, 78.96], "DE": [51.16, 10.45],
        "FR": [46.22, 2.21], "BR": [-14.23, -51.92], "CA": [56.13, -106.34],
        "AU": [-25.27, 133.77], "JP": [36.20, 138.25], "GB": [55.37, -3.43]
      };
      
      for(const [code, pos] of Object.entries(coords)){
        L.circleMarker(pos, { color: '#10b981', radius: 8, fillOpacity: 0.6 })
          .addTo(map).bindPopup(code)
          .on('click', () => {
             document.getElementById('location').value = code;
             handleLocationChange();
          });
      }
    }

    // --- FORM LOGIC ---
    function handleLocationChange() {
      const loc = document.getElementById('location').value;
      const indiaFields = document.getElementById('india-fields');
      
      if(loc === 'IN') {
        indiaFields.classList.remove('hidden');
      } else {
        indiaFields.classList.add('hidden');
      }
      
      fetchWeather(loc);
      fetchCarbonPrice(loc);
      
      const coords = {
        "US": [37.09, -95.71], "IN": [20.59, 78.96], "DE": [51.16, 10.45],
        "FR": [46.22, 2.21], "BR": [-14.23, -51.92], "CA": [56.13, -106.34],
        "AU": [-25.27, 133.77], "JP": [36.20, 138.25], "GB": [55.37, -3.43]
      };
      if(coords[loc]) map.flyTo(coords[loc], 4);
    }

    function handleStateChange() {
      const state = document.getElementById('state').value;
      const citySelect = document.getElementById('city');
      const cityWrapper = document.getElementById('city-wrapper');
      
      citySelect.innerHTML = '<option value="">Select City</option>';
      
      const list = citiesByState[state];
      if(list) {
        cityWrapper.classList.remove('hidden');
        list.forEach(c => {
           const opt = document.createElement('option');
           opt.value = c; opt.innerText = c;
           citySelect.appendChild(opt);
        });
      } else {
        cityWrapper.classList.add('hidden');
      }
    }

    function handleCityChange() {
      const city = document.getElementById('city').value;
      const townWrapper = document.getElementById('town-wrapper');
      if(city === 'Bidar') townWrapper.classList.remove('hidden');
      else townWrapper.classList.add('hidden');
    }

    function loadExample(loc, hrs, habits) {
      document.getElementById('location').value = loc;
      document.getElementById('daily_hours').value = hrs;
      document.getElementById('habits').value = habits;
      handleLocationChange();
    }

    // --- API CALLS ---
    async function fetchWeather(loc) {
      const res = await fetch(`/weather?location=${loc}`);
      const data = await res.json();
      if(data && data.temperature) {
        document.getElementById('weatherDisplay').classList.remove('hidden');
        document.getElementById('tempDisplay').innerText = `${data.temperature}°C`;
        document.getElementById('weatherDesc').innerText = data.description;
      }
    }

    async function fetchCarbonPrice(loc) {
      const res = await fetch('/carbon-price');
      const data = await res.json();
      const sym = loc === 'IN' ? '₹' : (loc === 'DE' ? '€' : '$'); 
      const val = loc === 'IN' ? data * 80 : data; 
      document.getElementById('carbonPriceDisplay').innerText = `${sym}${val.toFixed(2)}/ton`;
    }

    async function analyze() {
      const btn = document.querySelector('button[onclick="analyze()"]');
      const originalText = btn.innerHTML;
      btn.innerText = "Processing AI Analysis..."; btn.disabled = true;

      const payload = {
        location: document.getElementById('location').value,
        daily_hours: document.getElementById('daily_hours').value,
        habits: document.getElementById('habits').value,
        state: document.getElementById('state').value,
        city: document.getElementById('city').value,
        town: document.getElementById('town').value
      };

      try {
        const res = await fetch('/analyze', {
          method: 'POST', headers: {'Content-Type': 'application/json'},
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        
        if(data.error) { alert(data.error); return; }

        document.getElementById('results').classList.remove('hidden');
        
        // Populate results
        document.getElementById('res-carbon').innerText = data.carbon_footprint_kg;
        document.getElementById('res-trees').innerText = data.trees_needed;
        document.getElementById('res-savings').innerText = data.annual_savings;
        document.getElementById('res-payback').innerText = data.payback_period;
        document.getElementById('habits-summary').innerText = data.habits_summary;

        // Tags
        const tagsDiv = document.getElementById('profile-tags');
        tagsDiv.innerHTML = data.profile_tags.map(t => 
            `<span class="px-2 py-1 bg-emerald-500/20 text-emerald-400 border border-emerald-500/50 rounded text-xs font-bold">${t}</span>`
        ).join('');

        // Lists
        document.getElementById('action-list').innerHTML = data.action_plan.map(i => 
          `<li class="flex items-start gap-2"><i class="fas fa-arrow-right text-emerald-500 mt-1"></i><span>${i}</span></li>`
        ).join('');

        document.getElementById('renewable-list').innerHTML = data.renewable_recommendations.map(i => 
          `<li class="flex items-start gap-2"><i class="fas fa-bolt text-yellow-400 mt-1"></i><span>${i}</span></li>`
        ).join('');

        // Tips Grid
        document.getElementById('tips-grid').innerHTML = data.efficiency_tips.map(tip => 
            `<div class="p-3 bg-slate-800/50 rounded-lg text-sm text-slate-300 border-l-2 border-yellow-400">${tip}</div>`
        ).join('');
        
        document.getElementById('results').scrollIntoView({ behavior: 'smooth' });

      } catch(e) {
        console.error(e);
        alert("Error during analysis.");
      } finally {
        btn.innerHTML = originalText; btn.disabled = false;
      }
    }

    // --- ESTIMATOR CALLS ---
    async function calcSolar() {
        const payload = { location: document.getElementById('location').value, roof_size_sqft: document.getElementById('solarRoof').value };
        const res = await fetch('/solar-cost', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload) });
        const data = await res.json();
        document.getElementById('solar-res').classList.remove('hidden');
        document.getElementById('solar-cost').innerText = data.total_cost;
        document.getElementById('solar-save').innerText = data.annual_savings;
    }

    async function calcWind() {
        const payload = { location: document.getElementById('location').value, turbine_size_kw: document.getElementById('windSize').value };
        const res = await fetch('/wind-estimate', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload) });
        const data = await res.json();
        document.getElementById('wind-res').classList.remove('hidden');
        document.getElementById('wind-cost').innerText = data.total_cost;
        document.getElementById('wind-kwh').innerText = data.annual_energy_kwh;
    }

    async function calcHydro() {
        const payload = { 
            location: document.getElementById('location').value, 
            flow_rate_lps: document.getElementById('hydroFlow').value,
            head_height_m: document.getElementById('hydroHead').value
        };
        const res = await fetch('/hydro-estimate', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload) });
        const data = await res.json();
        document.getElementById('hydro-res').classList.remove('hidden');
        document.getElementById('hydro-cost').innerText = data.total_cost;
        document.getElementById('hydro-size').innerText = data.system_size_kw;
    }

    window.onload = function() {
      initMap();
      fetchWeather('US');
      fetchCarbonPrice('US');
    }
  </script>
</body>
</html>
'''

# --- BACKEND ROUTES ---

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE, 
                                india_states=INDIA_STATES, 
                                cities_by_state=CITIES_BY_STATE, 
                                bidar_towns=BIDAR_TOWNS,
                                examples=EXAMPLES)

@app.route('/weather')
def weather_route():
    loc = request.args.get('location', 'US')
    return jsonify(get_current_weather(loc) or {})

@app.route('/carbon-price')
def price_route():
    return jsonify(CARBON_PRICE_DEFAULT)

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    loc = data.get('location', 'US')
    habits = data.get('habits', '').lower()
    
    try:
        daily_hours = float(data.get('daily_hours', 0))
    except:
        return jsonify({"error": "Invalid hours"}), 400

    # 1. Advanced Load Calculation based on Habits
    # Base load assumption (kW)
    avg_load_kw = 0.5 
    
    profile_tags = [f"📍 {loc}"]
    
    # Keyword detection scoring
    if any(x in habits for x in ['ac', 'cooling', 'air con']):
        avg_load_kw += 1.5
        profile_tags.append("❄️ Heavy Cooling")
    if any(x in habits for x in ['heat', 'heater', 'winter']):
        avg_load_kw += 1.5
        profile_tags.append("🔥 Electric Heating")
    if any(x in habits for x in ['ev', 'tesla', 'car', 'vehicle']):
        avg_load_kw += 2.0
        profile_tags.append("🚗 EV Owner")
    if any(x in habits for x in ['office', 'wfh', 'computer', 'laptop']):
        avg_load_kw += 0.2
        profile_tags.append("💻 Remote Worker")
    
    # Calculate Monthly Consumption
    monthly_kwh = daily_hours * 30 * avg_load_kw
    
    if monthly_kwh > 800: profile_tags.append("⚡ High Consumer")
    else: profile_tags.append("🌱 Efficient Consumer")

    # 2. Carbon Math
    ci = CARBON_INTENSITY.get(loc, 450)
    carbon_kg = round((monthly_kwh * ci) / 1000, 2)
    trees = round(carbon_kg * 12 / 21)
    
    currency = CURRENCY_SYMBOL.get(loc, '$')
    rate = ELECTRICITY_RATE.get(loc, 0.15)
    
    # 3. Financials
    annual_cost = monthly_kwh * 12 * rate
    potential_savings = annual_cost * 0.30 # Target 30% reduction
    
    # 4. Generate Specific Tips & Action Plan
    tips = []
    action_plan = []
    
    # General Start
    action_plan.append("Day 1: Install a smart energy monitor to track peak usage.")

    if "ac" in habits or "cool" in habits:
        tips.extend(random.sample(ENERGY_TIPS['ac'], 2))
        action_plan.append("Day 5: Service AC filters and set thermostat to 24°C.")
    
    if "heat" in habits:
        tips.extend(random.sample(ENERGY_TIPS['heating'], 2))
        action_plan.append("Day 7: Seal window drafts to prevent heat loss.")
        
    if "ev" in habits:
        tips.extend(random.sample(ENERGY_TIPS['ev'], 2))
        action_plan.append("Day 10: Schedule EV charging for off-peak hours (10PM+).")
    
    if "office" in habits or "laptop" in habits:
        tips.extend(random.sample(ENERGY_TIPS['office'], 2))
        
    # Fill remaining tips
    while len(tips) < 4:
        tips.append(random.choice(ENERGY_TIPS['appliances'] + ENERGY_TIPS['lighting']))
    
    tips = list(set(tips))[:4] # Dedupe and limit

    # 5. Renewable Logic (Location Specific)
    renewables = []
    pot = RENEWABLE_POTENTIAL.get(loc, {"solar": "moderate", "wind": "low"})
    
    if pot['solar'] == 'excellent':
        renewables.append("☀️ Rooftop Solar: High potential. 5kW system can offset 90% usage.")
    elif pot['solar'] == 'good':
        renewables.append("☀️ Solar: Good ROI. Consider a 3-4kW system.")
    
    if pot['wind'] == 'excellent':
        renewables.append("💨 Micro-Wind: Feasible if you have open land.")
    
    if monthly_kwh > 600:
        renewables.append("🔋 Battery Storage: Essential for your high usage.")
    
    # Specific Bidar/India Logic
    town = data.get('town', '')
    if loc == "IN":
        action_plan.append("Day 15: Check 'PM Surya Ghar' scheme eligibility.")
        if town in BIDAR_TOWNS:
             renewables.insert(0, f"☀️ Bidar Specific: Excellent solar irradiance (5.2 kWh/m²). Priority investment.")
             profile_tags.append(f"📍 {town}")

    # Finalize Action Plan
    if len(action_plan) < 4:
        action_plan.append("Day 20: Switch all remaining bulbs to LED.")
        action_plan.append("Day 30: Review monthly bill for savings.")

    summary = f"Based on your {daily_hours} hours of daily activity and detected habits, we estimate a load of {avg_load_kw}kW, resulting in approx {int(monthly_kwh)} kWh/month."

    return jsonify({
        "carbon_footprint_kg": carbon_kg,
        "trees_needed": trees,
        "annual_savings": f"{currency}{potential_savings:,.0f}",
        "payback_period": "3-5" if "solar" in str(renewables).lower() else "1-2",
        "action_plan": action_plan,
        "renewable_recommendations": renewables,
        "efficiency_tips": tips,
        "profile_tags": profile_tags,
        "habits_summary": summary
    })

# Estimator Routes
@app.route('/solar-cost', methods=['POST'])
def solar_cost():
    d = request.json
    loc = d.get('location','US')
    curr = CURRENCY_SYMBOL.get(loc, '$')
    cost = 1000 if loc == 'IN' else 3000
    total = float(d.get('roof_size_sqft',500)) * 0.015 * cost 
    return jsonify({"total_cost": f"{curr}{total:,.0f}", "annual_savings": f"{curr}{total*0.15:,.0f}"})

@app.route('/wind-estimate', methods=['POST'])
def wind_estimate():
    d = request.json
    loc = d.get('location','US')
    curr = CURRENCY_SYMBOL.get(loc, '$')
    cost = 1200 if loc == 'IN' else 3500
    kw = float(d.get('turbine_size_kw',5))
    return jsonify({"total_cost": f"{curr}{kw*cost:,.0f}", "annual_energy_kwh": f"{kw*24*365*0.25:,.0f}"})

@app.route('/hydro-estimate', methods=['POST'])
def hydro_estimate():
    d = request.json
    loc = d.get('location','US')
    curr = CURRENCY_SYMBOL.get(loc, '$')
    kw = 9.81 * (float(d.get('flow_rate_lps',20))/1000) * float(d.get('head_height_m',5)) * 0.8
    cost_per_kw = 1500 if loc == 'IN' else 4000
    return jsonify({"system_size_kw": f"{kw:.2f}", "total_cost": f"{curr}{max(2000, kw*cost_per_kw):,.0f}"})

if __name__ == '__main__':
    app.run(debug=True, port=5000)