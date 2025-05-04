import requests
import time
import json
from datetime import datetime, timedelta
import threading
from flask import Flask, render_template, jsonify, request
from collections import deque
import math
import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import RealDictCursor
import os
from pywebpush import webpush, WebPushException
from flask_cors import CORS
from contextlib import contextmanager
import atexit
import re

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(24))

DATABASE_URL = os.environ.get('DATABASE_URL')

pool = ThreadedConnectionPool(
    minconn=1,
    maxconn=20,
    dsn=DATABASE_URL
)

VAPID_PRIVATE_KEY = os.environ.get('VAPID_PRIVATE_KEY')

VAPID_PUBLIC_KEY = os.environ.get('VAPID_PUBLIC_KEY')
VAPID_CLAIMS = {
    "sub": "mailto:ornek@gmail.com"
}

EMSC_URL = "https://www.seismicportal.eu/fdsnws/event/1/query?limit=100&format=json"
KANDILLI_URL = "http://www.koeri.boun.edu.tr/scripts/lst0.asp"
AFAD_URL = "https://deprem.afad.gov.tr/apiv2/event/filter"

TURKEY_LAT_MIN = 36.0
TURKEY_LAT_MAX = 42.1
TURKEY_LON_MIN = 26.0
TURKEY_LON_MAX = 45.0

TURKEY_CITIES = {
    "Adana": (37.0000, 35.3213),
    "Adıyaman": (37.7648, 38.2786),
    "Afyonkarahisar": (38.7507, 30.5567),
    "Ağrı": (39.7191, 43.0503),
    "Amasya": (40.6499, 35.8353),
    "Ankara": (39.9208, 32.8541),
    "Antalya": (36.8969, 30.7133),
    "Artvin": (41.1828, 41.8183),
    "Aydın": (37.8444, 27.8458),
    "Balıkesir": (39.6484, 27.8826),
    "Bilecik": (40.1500, 29.9833),
    "Bingöl": (38.8854, 40.4983),
    "Bitlis": (38.4001, 42.1095),
    "Bolu": (40.7395, 31.6061),
    "Burdur": (37.7200, 30.2900),
    "Bursa": (40.1826, 29.0665),
    "Çanakkale": (40.1553, 26.4142),
    "Çankırı": (40.6013, 33.6134),
    "Çorum": (40.5506, 34.9556),
    "Denizli": (37.7765, 29.0864),
    "Diyarbakır": (37.9144, 40.2306),
    "Edirne": (41.6771, 26.5557),
    "Elazığ": (38.6810, 39.2264),
    "Erzincan": (39.7500, 39.5000),
    "Erzurum": (39.9043, 41.2679),
    "Eskişehir": (39.7767, 30.5206),
    "Gaziantep": (37.0662, 37.3833),
    "Giresun": (40.9128, 38.3895),
    "Gümüşhane": (40.4386, 39.5086),
    "Hakkari": (37.5744, 43.7408),
    "Hatay": (36.2021, 36.1608),
    "Isparta": (37.7648, 30.5566),
    "Mersin": (36.8000, 34.6333),
    "İstanbul": (41.0082, 28.9784),
    "İzmir": (38.4192, 27.1287),
    "Kars": (40.6167, 43.0975),
    "Kastamonu": (41.3887, 33.7827),
    "Kayseri": (38.7312, 35.4787),
    "Kırklareli": (41.7333, 27.2167),
    "Kırşehir": (39.1425, 34.1709),
    "Kocaeli": (40.8533, 29.8815),
    "Konya": (37.8667, 32.4833),
    "Kütahya": (39.4167, 29.9833),
    "Malatya": (38.3552, 38.3095),
    "Manisa": (38.6191, 27.4289),
    "Kahramanmaraş": (37.5736, 36.9371),
    "Mardin": (37.3212, 40.7245),
    "Muğla": (37.2153, 28.3636),
    "Muş": (38.7325, 41.4916),
    "Nevşehir": (38.6939, 34.6857),
    "Niğde": (37.9667, 34.6833),
    "Ordu": (40.9839, 37.8764),
    "Rize": (41.0201, 40.5234),
    "Sakarya": (40.7569, 30.3781),
    "Samsun": (41.2928, 36.3313),
    "Siirt": (37.9333, 41.9500),
    "Sinop": (42.0231, 35.1531),
    "Sivas": (39.7477, 37.0179),
    "Tekirdağ": (40.9833, 27.5167),
    "Tokat": (40.3167, 36.5500),
    "Trabzon": (41.0015, 39.7178),
    "Tunceli": (39.1079, 39.5401),
    "Şanlıurfa": (37.1591, 38.7969),
    "Uşak": (38.6823, 29.4082),
    "Van": (38.4891, 43.4089),
    "Yozgat": (39.8181, 34.8147),
    "Zonguldak": (41.4564, 31.7987),
    "Aksaray": (38.3687, 34.0370),
    "Bayburt": (40.2552, 40.2249),
    "Karaman": (37.1759, 33.2287),
    "Kırıkkale": (39.8468, 33.5153),
    "Batman": (37.8812, 41.1351),
    "Şırnak": (37.5164, 42.4611),
    "Bartın": (41.6344, 32.3375),
    "Ardahan": (41.1105, 42.7022),
    "Iğdır": (39.9167, 44.0333),
    "Yalova": (40.6500, 29.2667),
    "Karabük": (41.2061, 32.6204),
    "Kilis": (36.7184, 37.1212),
    "Osmaniye": (37.0742, 36.2478),
    "Düzce": (40.8438, 31.1565)
}

PROVINCE_BOUNDARIES = {
    "Kütahya": [38.9, 39.8, 28.9, 30.3], 
    "Uşak": [38.3, 38.9, 28.8, 29.9],     
    "Afyonkarahisar": [38.2, 39.2, 29.9, 31.5],
    "Manisa": [38.2, 39.3, 27.2, 28.9],
    "Denizli": [37.4, 38.4, 28.6, 29.9],
    "Balıkesir": [39.1, 40.3, 26.7, 28.9],
    "Bursa": [39.8, 40.4, 28.2, 30.0],
    "Bilecik": [39.8, 40.4, 29.7, 30.6],
    "Eskişehir": [39.1, 40.1, 30.1, 31.7],
    "İzmir": [37.8, 39.1, 26.2, 28.2],
    "Aydın": [37.3, 38.2, 27.2, 28.9],
    "Muğla": [36.3, 37.6, 27.2, 29.4],
    "Burdur": [36.9, 37.8, 29.4, 30.9],
    "Isparta": [37.4, 38.5, 30.0, 31.5],
    "Antalya": [36.0, 37.6, 29.3, 32.5],
    "Konya": [36.5, 39.5, 31.0, 34.5],
    "Karaman": [36.7, 37.7, 32.3, 34.1],
    "Mersin": [36.0, 37.5, 32.5, 35.0],
    "Adana": [36.5, 38.2, 34.5, 36.5],
    "Niğde": [37.2, 38.4, 34.0, 35.5],
    "Aksaray": [38.0, 39.0, 33.0, 34.5],
    "Nevşehir": [38.4, 39.2, 34.0, 35.2],
    "Kırşehir": [38.8, 39.8, 33.5, 34.8],
    "Kayseri": [37.7, 39.2, 35.0, 36.8],
    "Yozgat": [38.8, 40.2, 34.0, 36.2],
    "Tokat": [39.8, 40.8, 35.5, 37.5],
    "Sivas": [38.5, 40.6, 36.0, 39.0],
    "Kahramanmaraş": [37.2, 38.8, 36.0, 37.6],
    "Osmaniye": [36.9, 37.8, 35.7, 36.5],
    "Gaziantep": [36.6, 37.5, 36.5, 38.0],
    "Kilis": [36.5, 37.0, 36.5, 37.5],
    "Hatay": [35.8, 37.0, 35.8, 36.7],
    "Adıyaman": [37.5, 38.5, 37.5, 39.0],
    "Şanlıurfa": [36.7, 38.0, 37.8, 40.2],
    "Diyarbakır": [37.3, 38.7, 39.5, 41.5],
    "Mardin": [36.9, 37.6, 40.0, 41.8],
    "Batman": [37.5, 38.3, 40.5, 41.5],
    "Siirt": [37.5, 38.5, 41.5, 42.6],
    "Şırnak": [37.0, 37.8, 42.0, 43.5],
    "Van": [37.5, 39.2, 42.5, 44.5],
    "Bitlis": [38.0, 39.0, 41.5, 43.0],
    "Muş": [38.5, 39.5, 41.0, 42.0],
    "Bingöl": [38.5, 39.5, 40.0, 41.5],
    "Elazığ": [38.3, 39.5, 38.3, 40.3],
    "Malatya": [37.8, 39.0, 37.0, 39.0],
    "Tunceli": [38.8, 39.6, 39.0, 40.5],
    "Erzincan": [39.0, 40.3, 38.5, 40.5],
    "Erzurum": [39.5, 41.0, 40.0, 42.5],
    "Ağrı": [39.0, 40.0, 42.5, 44.5],
    "Iğdır": [39.5, 40.2, 43.5, 44.8],
    "Kars": [40.0, 41.4, 42.0, 44.0],
    "Ardahan": [40.8, 41.6, 42.0, 43.3],
    "Artvin": [40.8, 41.5, 41.0, 42.5],
    "Rize": [40.5, 41.2, 40.0, 41.5],
    "Trabzon": [40.5, 41.2, 39.0, 40.5],
    "Giresun": [40.0, 41.0, 37.8, 39.5],
    "Ordu": [40.5, 41.2, 36.5, 38.2],
    "Gümüşhane": [40.0, 40.7, 38.5, 40.0],
    "Bayburt": [40.0, 40.8, 39.6, 40.5],
    "Samsun": [40.8, 41.8, 35.0, 37.0],
    "Amasya": [40.3, 41.0, 35.0, 36.5],
    "Çorum": [40.0, 41.3, 34.0, 35.5],
    "Kastamonu": [41.0, 42.0, 32.5, 34.5],
    "Sinop": [41.5, 42.2, 34.5, 35.5],
    "Çankırı": [40.3, 41.2, 32.5, 34.0],
    "Karabük": [40.8, 41.5, 32.0, 33.0],
    "Bartın": [41.3, 41.9, 32.0, 33.0],
    "Zonguldak": [41.0, 41.6, 31.0, 32.2],
    "Düzce": [40.6, 41.1, 30.8, 31.8],
    "Bolu": [40.3, 41.1, 30.5, 32.0],
    "Sakarya": [40.3, 41.1, 29.8, 31.0],
    "Kocaeli": [40.5, 41.2, 29.3, 30.3],
    "Yalova": [40.5, 40.8, 28.7, 29.5],
    "İstanbul": [40.7, 41.7, 27.9, 29.9],
    "Tekirdağ": [40.5, 41.5, 26.5, 28.2],
    "Kırklareli": [41.0, 42.0, 26.2, 28.0],
    "Edirne": [40.5, 41.8, 26.0, 27.0],
    "Çanakkale": [39.5, 40.7, 25.8, 27.5],
    "Ankara": [39.0, 40.5, 31.5, 33.5],
    "Kırıkkale": [39.3, 40.2, 33.3, 34.2]
}

SPECIAL_REGIONS = [
    [38.9, 39.3, 28.7, 29.1, "Kütahya"],  
]

recent_earthquakes = deque(maxlen=100)
earthquake_ids = set()
push_subscriptions = []
last_request_time = 0
MIN_REQUEST_INTERVAL = 1

@contextmanager
def get_db_connection():
    global pool
    conn = None
    try:
        conn = pool.getconn()
        yield conn
    except Exception as e:
        print(f"Error getting connection: {e}")
        if isinstance(e, psycopg2.pool.PoolError) and "closed" in str(e):
            pool = ThreadedConnectionPool(
                minconn=1,
                maxconn=20,
                dsn=DATABASE_URL
            )
            conn = pool.getconn()
            yield conn
        else:
            raise
    finally:
        if conn:
            try:
                pool.putconn(conn)
            except Exception as e:
                print(f"Error returning connection to pool: {e}")

def init_db():
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS earthquakes (
                id TEXT PRIMARY KEY, 
                magnitude REAL,
                place TEXT,
                nearest_city TEXT,
                distance_km REAL,
                lat REAL,
                lon REAL,
                depth REAL,
                time TIMESTAMP WITH TIME ZONE,
                detected_at TIMESTAMP WITH TIME ZONE,
                source TEXT
            )
        ''')
        
        cur.execute('CREATE INDEX IF NOT EXISTS idx_time ON earthquakes(time)')
        cur.execute('CREATE INDEX IF NOT EXISTS idx_magnitude ON earthquakes(magnitude)')
        cur.execute('CREATE INDEX IF NOT EXISTS idx_nearest_city ON earthquakes(nearest_city)')
        
        conn.commit()
        cur.close()

def save_earthquake_to_db(earthquake_data):
    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute('''
                INSERT INTO earthquakes 
                (id, magnitude, place, nearest_city, distance_km, lat, lon, depth, time, detected_at, source)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    magnitude = EXCLUDED.magnitude,
                    place = EXCLUDED.place,
                    nearest_city = EXCLUDED.nearest_city,
                    distance_km = EXCLUDED.distance_km,
                    lat = EXCLUDED.lat,
                    lon = EXCLUDED.lon,
                    depth = EXCLUDED.depth,
                    time = EXCLUDED.time,
                    detected_at = EXCLUDED.detected_at,
                    source = EXCLUDED.source
            ''', (
                earthquake_data['id'], 
                earthquake_data['magnitude'], 
                earthquake_data['place'], 
                earthquake_data['nearest_city'],
                earthquake_data['distance_km'], 
                earthquake_data['lat'],
                earthquake_data['lon'], 
                earthquake_data.get('depth', 0),
                earthquake_data['time'], 
                earthquake_data['detected_at'],
                earthquake_data.get('source', 'UNKNOWN')
            ))
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Error saving earthquake to DB: {e}")
        finally:
            cur.close()

def send_push_notification(earthquake_data):
    for subscription in push_subscriptions[:]:
        try:
            webpush(
                subscription_info=subscription,
                data=json.dumps({
                    'title': f'Deprem: M{earthquake_data["magnitude"]}',
                    'body': f'{earthquake_data["nearest_city"]} yakınlarında deprem! Büyüklük: {earthquake_data["magnitude"]}, Mesafe: {earthquake_data["distance_km"]} km'
                }),
                vapid_private_key=VAPID_PRIVATE_KEY,
                vapid_claims=VAPID_CLAIMS
            )
        except WebPushException as e:
            print(f"Push notification failed: {e}")
            push_subscriptions.remove(subscription)

def fetch_emsc_earthquakes():
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(EMSC_URL, timeout=10, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            return data.get('features', [])
        return []
    except:
        return []

def fetch_kandilli_earthquakes():
    try:
        response = requests.get(KANDILLI_URL, timeout=10)
        response.encoding = 'windows-1254'
        
        if response.status_code == 200:
            earthquakes = []
            content = response.text
            
            pre_pattern = r"<pre>(.*?)</pre>"
            pre_match = re.search(pre_pattern, content, re.DOTALL)
            
            if pre_match:
                data_lines = pre_match.group(1).split('\n')
                
                for line in data_lines:
                    if not line.strip():
                        continue
                    
                    if 'MD' in line and 'ML' in line and 'Mw' in line:
                        continue
                    
                    parts = line.split()
                    
                    if len(parts) > 12:
                        try:
                            date = parts[0]
                            time = parts[1]
                            
                            dt_str = f"{date} {time}"
                            try:
                                dt = datetime.strptime(dt_str, "%Y.%m.%d %H:%M:%S")
                            except:
                                continue
                            
                            lat = float(parts[2])
                            lon = float(parts[3])
                            depth = float(parts[4])
                            
                            ml = float(parts[6]) if parts[6] != '-.-' else 0
                            mw = float(parts[7]) if parts[7] != '-.-' else 0
                            magnitude = max(ml, mw)
                            
                            if magnitude == 0:
                                continue
                            
                            place_parts = parts[8:]
                            for i, part in enumerate(place_parts):
                                if part in ['İlksel', 'REVIZE01', 'REVIZE02']:
                                    place = ' '.join(place_parts[:i])
                                    break
                            else:
                                place = ' '.join(place_parts)
                            
                            earthquake_data = {
                                'id': f"kandilli_{dt.strftime('%Y%m%d%H%M%S')}_{lat}_{lon}",
                                'time': dt,
                                'lat': lat,
                                'lon': lon,
                                'depth': depth,
                                'magnitude': magnitude,
                                'place': place,
                                'source': 'KANDILLI'
                            }
                            
                            earthquakes.append(earthquake_data)
                        except:
                            continue
            
            return earthquakes
    except Exception as e:
        print(f"Error fetching Kandilli data: {e}")
        return []

def fetch_afad_earthquakes():
    try:
        end_time = datetime.now()
        start_time = end_time - timedelta(days=1)
        
        params = {
            'start': start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'end': end_time.strftime('%Y-%m-%d %H:%M:%S'),
            'minlat': 36.0,
            'maxlat': 42.1,
            'minlon': 26.0,
            'maxlon': 45.0,
            'format': 'json'
        }
        
        response = requests.get(AFAD_URL, params=params, timeout=10)
        
        if response.status_code == 200:
            earthquakes = []
            data = response.json()
            
            for quake in data:
                date_str = quake.get('date', '')
                try:
                    if 'T' in date_str:
                        quake_time = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S')
                    else:
                        quake_time = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                except:
                    quake_time = datetime.now()
                
                earthquake_data = {
                    'id': f"afad_{quake.get('earthquake_id', '')}",
                    'magnitude': float(quake.get('magnitude', 0)),
                    'place': quake.get('location', ''),
                    'lat': float(quake.get('latitude', 0)),
                    'lon': float(quake.get('longitude', 0)),
                    'depth': float(quake.get('depth', 0)),
                    'time': quake_time,
                    'source': 'AFAD'
                }
                earthquakes.append(earthquake_data)
            
            return earthquakes
        return []
    except Exception as e:
        print(f"Error fetching AFAD data: {e}")
        return []
    
def is_in_turkey(lat, lon):
    return (TURKEY_LAT_MIN <= lat <= TURKEY_LAT_MAX) and (TURKEY_LON_MIN <= lon <= TURKEY_LON_MAX)

def haversine_distance(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371  
    return c * r

def is_in_special_region(lat, lon):
    for region in SPECIAL_REGIONS:
        min_lat, max_lat, min_lon, max_lon, province = region
        if min_lat <= lat <= max_lat and min_lon <= lon <= max_lon:
            return province, 0  
    return None, None

def is_within_province(lat, lon, province_boundaries):
    min_lat, max_lat, min_lon, max_lon = province_boundaries
    return min_lat <= lat <= max_lat and min_lon <= lon <= max_lon

def find_nearest_city(lat, lon):
    
    special_province, distance = is_in_special_region(lat, lon)
    if special_province:
        return special_province, distance
    
    matching_provinces = []
    for province, boundaries in PROVINCE_BOUNDARIES.items():
        if is_within_province(lat, lon, boundaries):
            matching_provinces.append(province)
    
    if len(matching_provinces) == 1:
        city_lat, city_lon = TURKEY_CITIES[matching_provinces[0]]
        distance = haversine_distance(lat, lon, city_lat, city_lon)
        return matching_provinces[0], round(distance, 1)
    
    elif len(matching_provinces) > 1:
        min_distance = float('inf')
        nearest_province = None
        
        for province in matching_provinces:
            city_lat, city_lon = TURKEY_CITIES[province]
            distance = haversine_distance(lat, lon, city_lat, city_lon)
            if distance < min_distance:
                min_distance = distance
                nearest_province = province
        
        return nearest_province, round(min_distance, 1)
    
    min_distance = float('inf')
    nearest_city = None
    
    for city, (city_lat, city_lon) in TURKEY_CITIES.items():
        distance = haversine_distance(lat, lon, city_lat, city_lon)
        if distance < min_distance:
            min_distance = distance
            nearest_city = city
    
    return nearest_city, round(min_distance, 1)

def process_earthquakes():
    global earthquake_ids
    
    emsc_earthquakes = fetch_emsc_earthquakes()
    kandilli_earthquakes = fetch_kandilli_earthquakes()
    afad_earthquakes = fetch_afad_earthquakes()
    
    all_earthquakes = []
    
    for quake in emsc_earthquakes:
        quake_id = quake.get('id')
        properties = quake.get('properties', {})
        geometry = quake.get('geometry', {})
        coords = geometry.get('coordinates', [None, None, None])

        if len(coords) >= 2:
            lon = coords[0]
            lat = coords[1]
            depth = coords[2] if len(coords) > 2 else 0
            mag = properties.get('mag')
            place = properties.get('flynn_region')
            time_occurred = properties.get('time')

            if is_in_turkey(lat, lon):
                try:
                    dt = datetime.strptime(time_occurred, "%Y-%m-%dT%H:%M:%S.%fZ")
                except:
                    try:
                        dt = datetime.strptime(time_occurred, "%Y-%m-%d %H:%M:%S UTC")
                    except:
                        dt = datetime.now()

                earthquake_data = {
                    'id': f"emsc_{quake_id}",
                    'magnitude': mag,
                    'place': place,
                    'lat': lat,
                    'lon': lon,
                    'depth': depth,
                    'time': dt,
                    'source': 'EMSC'
                }
                
                all_earthquakes.append(earthquake_data)
    
    all_earthquakes.extend(kandilli_earthquakes)
    all_earthquakes.extend(afad_earthquakes)
    
    for earthquake_data in all_earthquakes:
        quake_id = earthquake_data['id']
        
        if quake_id not in earthquake_ids:
            nearest_city, distance_km = find_nearest_city(earthquake_data['lat'], earthquake_data['lon'])
            
            earthquake_data['nearest_city'] = nearest_city
            earthquake_data['distance_km'] = distance_km
            earthquake_data['detected_at'] = datetime.now()
            
            recent_earthquakes.appendleft(earthquake_data)
            earthquake_ids.add(quake_id)
            save_earthquake_to_db(earthquake_data)
            
            if earthquake_data['magnitude'] >= 3.0:
                send_push_notification(earthquake_data)
            
            if len(earthquake_ids) > 1000:
                oldest_id = next(iter(earthquake_ids))
                earthquake_ids.remove(oldest_id)

def background_task():
    while True:
        try:
            print("Fetching and processing earthquakes...")
            process_earthquakes()
        except Exception as e:
            print(f"Error in background task: {e}")
        time.sleep(30)

@app.route('/')
def index():
    return render_template('index.html', 
                         turkey_cities=TURKEY_CITIES, 
                         vapid_public_key=VAPID_PUBLIC_KEY)

@app.route('/api/earthquakes')
def get_earthquakes():
    limit = request.args.get('limit', 150, type=int)
    
    with get_db_connection() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        query = "SELECT * FROM earthquakes ORDER BY time DESC LIMIT %s"
        cur.execute(query, (limit,))
        results = cur.fetchall()
        cur.close()
        
        for result in results:
            if result['time']:
                result['time'] = result['time'].strftime("%Y-%m-%d %H:%M:%S UTC")
            if result['detected_at']:
                result['detected_at'] = result['detected_at'].strftime("%Y-%m-%d %H:%M:%S")
        
        return jsonify(results)

@app.route('/api/push/subscribe', methods=['POST'])
def subscribe_push():
    subscription = request.json
    if subscription not in push_subscriptions:
        push_subscriptions.append(subscription)
    return jsonify({'success': True})

@app.route('/sw.js')
def service_worker():
    return app.send_static_file('sw.js')

@app.route('/manifest.json')
def manifest():
    return app.send_static_file('manifest.json')

@app.route('/sitemap1.xml')
def sitemap():
    return app.send_static_file('sitemap.xml')

@app.route('/robots.txt')
def robots():
    return app.send_static_file('robots.txt')

@app.errorhandler(404)
def not_found_error(error):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

@atexit.register
def shutdown():
    print("Shutting down connection pool...")
    pool.closeall()

if __name__ == "__main__":
    init_db()
    thread = threading.Thread(target=background_task, daemon=True)
    thread.start()
    app.run(host='0.0.0.0', port=5000, debug=False)