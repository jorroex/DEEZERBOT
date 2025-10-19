import os
import nest_asyncio
import glob
import time
import requests
import json
import subprocess
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

# ✅ Configuración
TOKEN = "8224886806:AAHM0sU3_xix-UgIcKq737fZ1TdqnwAMraQ"
ARL = "cc633fa89fdb7853ab5e9d87f04b002370dc46b0de785e2752ca968e598ad230a5f43bcd9a50c456dc7ff4a999a709bf159d4562f9df2b81bb3a64f278c449e0675f327209c5ee9a9694dbb7e02a9f2320efa87f58e75c4f5f650c8830d59990"

# Carpetas de descargas
DOWNLOAD_DIR = "deezer_downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Instalar dependencias necesarias
def instalar_dependencias():
    print("📦 Instalando dependencias...")
    try:
        subprocess.run(["pip", "install", "deemix"], check=True, capture_output=True)
        print("✅ deemix instalado correctamente")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error instalando deemix: {e}")

# Instalar dependencias al inicio
instalar_dependencias()

# Configurar deemix
config_dir = os.path.expanduser("~/.config/deemix")
os.makedirs(config_dir, exist_ok=True)

config_content = {
    "arl": ARL,
    "downloadLocation": DOWNLOAD_DIR,
    "maxBitrate": "9",
    "fallbackBitrate": True,
    "createArtistFolder": True,
    "createAlbumFolder": False,
    "createCDFolder": False,
    "padTracks": True,
    "paddingSize": "0",
    "illegalCharacterReplacer": "_",
    "queueConcurrency": 3,
    "overwriteFile": "y",
    "saveArtwork": True,
    "downloadLyrics": True,
    "syncedLyrics": True,
    "embedLyrics": True,
    "tracknameTemplate": "%artist% - %title%",
    "albumTracknameTemplate": "%tracknumber% - %title%"
}

with open(os.path.join(config_dir, "config.json"), "w") as f:
    json.dump(config_content, f, indent=2)

# Aplicación de Telegram
nest_asyncio.apply()
application = ApplicationBuilder().token(TOKEN).build()

# Headers MEJORADOS para Deezer
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.deezer.com/",
    "Origin": "https://www.deezer.com",
    "DNT": "1",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
    "Cache-Control": "no-cache"
}

# Headers con ARL para endpoints privados
HEADERS_WITH_ARL = HEADERS.copy()
HEADERS_WITH_ARL["Cookie"] = f"arl={ARL}"

# 📌 FUNCIONES DE BÚSQUEDA MEJORADAS
def buscar_cancion(query, limit=10, index=0):
    try:
        print(f"🔍 [BUSQUEDA] Buscando canción: {query}")

        # Codificar la query para URL
        query_encoded = requests.utils.quote(query)
        url = f"https://api.deezer.com/search/track?q={query_encoded}&index={index}&limit={limit}"

        print(f"🔍 [API] URL: {url}")

        res = requests.get(url, headers=HEADERS, timeout=15)
        print(f"🔍 [API] Status Code: {res.status_code}")

        if res.status_code == 200:
            data = res.json()
            resultados = data.get("data", [])
            print(f"🔍 [API] Resultados encontrados: {len(resultados)}")

            # Debug: mostrar primeros resultados
            for i, resultado in enumerate(resultados[:3]):
                titulo = resultado.get('title', 'Sin título')
                artista = resultado.get('artist', {}).get('name', 'Artista desconocido')
                print(f"🔍 [API] Resultado {i+1}: {titulo} - {artista}")

            return resultados
        else:
            print(f"❌ [API] Error en la respuesta: {res.status_code}")
            return []
    except Exception as e:
        print(f"❌ [API] Error en búsqueda de canción: {e}")
        return []

def buscar_artista(query, limit=10, index=0):
    try:
        print(f"🔍 [ARTISTA] Buscando artista: {query}")

        query_encoded = requests.utils.quote(query)
        url = f"https://api.deezer.com/search/artist?q={query_encoded}&index=0&limit=1"

        res = requests.get(url, headers=HEADERS, timeout=15)
        print(f"🔍 [ARTISTA] Status Code: {res.status_code}")

        if res.status_code == 200:
            artistas = res.json().get("data", [])
            if not artistas:
                print("❌ [ARTISTA] No se encontró el artista")
                return []

            artist_id = artistas[0]["id"]
            print(f"🔍 [ARTISTA] ID encontrado: {artist_id}")

            url = f"https://api.deezer.com/artist/{artist_id}/top?limit={limit}"
            res = requests.get(url, headers=HEADERS, timeout=15)

            if res.status_code == 200:
                resultados = res.json().get("data", [])
                print(f"🔍 [ARTISTA] Canciones encontradas: {len(resultados)}")
                return resultados
        return []
    except Exception as e:
        print(f"❌ [ARTISTA] Error en búsqueda de artista: {e}")
        return []

def buscar_album(query, limit=10, index=0):
    try:
        print(f"🔍 [ALBUM] Buscando álbum: {query}")

        query_encoded = requests.utils.quote(query)
        url = f"https://api.deezer.com/search/album?q={query_encoded}&index=0&limit=1"

        res = requests.get(url, headers=HEADERS, timeout=15)
        print(f"🔍 [ALBUM] Status Code: {res.status_code}")

        if res.status_code == 200:
            albums = res.json().get("data", [])
            if not albums:
                print("❌ [ALBUM] No se encontró el álbum")
                return []

            album_id = albums[0]["id"]
            print(f"🔍 [ALBUM] ID encontrado: {album_id}")

            url = f"https://api.deezer.com/album/{album_id}/tracks"
            res = requests.get(url, headers=HEADERS, timeout=15)

            if res.status_code == 200:
                resultados = res.json().get("data", [])
                print(f"🔍 [ALBUM] Canciones encontradas: {len(resultados)}")
                return resultados
        return []
    except Exception as e:
        print(f"❌ [ALBUM] Error en búsqueda de álbum: {e}")
        return []

# 📌 FUNCIÓN PARA OBTENER INFORMACIÓN DE CANCIÓN
def obtener_info_cancion(track_id):
    try:
        url = f"https://api.deezer.com/track/{track_id}"
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            return res.json()
        return None
    except Exception as e:
        print(f"❌ Error obteniendo info de canción: {e}")
        return None

# 📌 SISTEMA MEJORADO DE BÚSQUEDA DE LETRAS DEEZER
def buscar_letras_deezer_profundo(track_id, track_info):
    """Búsqueda profunda de letras en Deezer usando múltiples endpoints"""
    titulo = track_info.get('title', '')
    artista = track_info.get('artist', {}).get('name', '')

    print(f"🔍 [DEEZER PROFUNDO] Buscando letras para: {artista} - {titulo} (ID: {track_id})")

    letras = None
    metodo = "No encontradas"

    # MÉTODO 1: Endpoint oficial de lyrics con ARL
    try:
        url = f"https://www.deezer.com/ajax/gw-light.php?method=song.getLyrics&api_version=1.0&api_token=&sid="
        payload = {
            "sng_id": track_id
        }

        response = requests.post(
            url,
            json=payload,
            headers=HEADERS_WITH_ARL,
            timeout=15
        )

        if response.status_code == 200:
            data = response.json()
            print(f"📡 [DEEZER LYRICS] Respuesta: {json.dumps(data, indent=2)[:500]}...")

            if 'results' in data and data['results']:
                lyrics_data = data['results'].get('LYRICS', {})
                if lyrics_data and lyrics_data.get('LYRICS_TEXT'):
                    letras = lyrics_data['LYRICS_TEXT'].strip()
                    if letras and len(letras) > 50:
                        print("✅ [DEEZER LYRICS] Letras encontradas vía endpoint oficial")
                        metodo = "Deezer Lyrics API"
                        return letras, metodo

                # Buscar letras sincronizadas
                if lyrics_data and lyrics_data.get('LYRICS_SYNC_JSON'):
                    sync_data = lyrics_data['LYRICS_SYNC_JSON']
                    if isinstance(sync_data, list) and len(sync_data) > 0:
                        # Convertir letras sincronizadas a texto plano
                        letras_sync = ""
                        for line in sync_data:
                            if 'lrc_timestamp' in line and 'text' in line:
                                timestamp = line['lrc_timestamp']
                                text = line['text'].strip()
                                if text:
                                    letras_sync += f"[{timestamp}] {text}\n"

                        if letras_sync:
                            print("✅ [DEEZER LYRICS] Letras sincronizadas encontradas")
                            metodo = "Deezer Sync Lyrics"
                            return letras_sync, metodo
    except Exception as e:
        print(f"❌ [DEEZER LYRICS] Error en endpoint oficial: {e}")

    # MÉTODO 2: API tradicional de Deezer
    try:
        url = f"https://api.deezer.com/track/{track_id}"
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'lyrics' in data and data['lyrics']:
                lyrics_data = data['lyrics']
                if 'text' in lyrics_data and lyrics_data['text']:
                    letras = lyrics_data['text'].strip()
                    if letras and len(letras) > 50:
                        print("✅ [DEEZER API] Letras encontradas vía API tradicional")
                        metodo = "API Deezer Tradicional"
                        return letras, metodo
    except Exception as e:
        print(f"❌ [DEEZER API] Error API tradicional: {e}")

    # MÉTODO 3: Endpoint mobile de Deezer
    try:
        url = f"https://api.deezer.com/track/{track_id}/lyrics"
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'lyrics' in data and data['lyrics']:
                body = data['lyrics'].get('body', '').strip()
                if body and len(body) > 50:
                    letras = body
                    print("✅ [DEEZER MOBILE] Letras encontradas vía endpoint mobile")
                    metodo = "Endpoint Mobile"
                    return letras, metodo
    except Exception as e:
        print(f"❌ [DEEZER MOBILE] Error endpoint mobile: {e}")

    return letras, metodo

# 📌 SISTEMA AVANZADO DE BÚSQUEDA DE LETRAS (MEJORADO)
def buscar_letras_avanzado(track_info):
    """Sistema avanzado de búsqueda de letras con enfoque en Deezer"""
    titulo = track_info.get('title', '')
    artista = track_info.get('artist', {}).get('name', '')
    track_id = track_info.get('id', '')

    print(f"🔍 [LETRAS AVANZADO] Buscando letras para: {artista} - {titulo} (ID: {track_id})")

    # PRIMERO: Búsqueda profunda en Deezer
    letras_deezer, metodo_deezer = buscar_letras_deezer_profundo(track_id, track_info)
    if letras_deezer:
        return letras_deezer, metodo_deezer

    # SEGUNDO: Fuentes externas (solo si Deezer falla)
    letras = None
    metodo = "No encontradas"

    # MÉTODO 4: Genius API
    try:
        letras_genius = buscar_genius(artista, titulo)
        if letras_genius:
            print("✅ [LETRAS] Encontradas vía Genius")
            metodo = "Genius"
            return letras_genius, metodo
    except Exception as e:
        print(f"❌ [LETRAS] Error Genius: {e}")

    # MÉTODO 5: AZLyrics (scraping)
    try:
        letras_az = buscar_azlyrics(artista, titulo)
        if letras_az:
            print("✅ [LETRAS] Encontradas vía AZLyrics")
            metodo = "AZLyrics"
            return letras_az, metodo
    except Exception as e:
        print(f"❌ [LETRAS] Error AZLyrics: {e}")

    return letras, metodo

# 📌 FUNCIONES EXTERNAS PARA LETRAS
def buscar_genius(artista, titulo):
    """Buscar letras en Genius"""
    try:
        query = f"{artista} {titulo}".replace(' ', '%20')
        search_url = f"https://genius.com/api/search/multi?q={query}"

        response = requests.get(search_url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            data = response.json()

            for section in data.get('response', {}).get('sections', []):
                if section.get('type') == 'song':
                    for hit in section.get('hits', [])[:3]:
                        result = hit.get('result', {})
                        song_url = result.get('url')

                        if song_url:
                            song_response = requests.get(song_url, headers=HEADERS, timeout=10)
                            if song_response.status_code == 200:
                                html_content = song_response.text
                                lyrics_pattern = r'<div[^>]*class="[^"]*Lyrics__Container[^"]*"[^>]*>([\s\S]*?)<\/div>'
                                matches = re.findall(lyrics_pattern, html_content)

                                if matches:
                                    letras = ""
                                    for match in matches:
                                        clean_lyrics = re.sub(r'<[^>]*>', '', match)
                                        clean_lyrics = re.sub(r'\[.*?\]', '', clean_lyrics)
                                        letras += clean_lyrics.strip() + "\n\n"

                                    if letras.strip():
                                        return letras.strip()[:3000]
    except Exception as e:
        print(f"❌ Error en Genius: {e}")

    return None

def buscar_azlyrics(artista, titulo):
    """Buscar letras en AZLyrics"""
    try:
        artista_clean = re.sub(r'[^a-zA-Z0-9]', '', artista.lower())
        titulo_clean = re.sub(r'[^a-zA-Z0-9]', '', titulo.lower())
        url = f"https://www.azlyrics.com/lyrics/{artista_clean}/{titulo_clean}.html"

        headers_az = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.azlyrics.com/'
        }

        response = requests.get(url, headers=headers_az, timeout=10)
        if response.status_code == 200:
            html_content = response.text
            lyrics_pattern = r'<!-- Usage of azlyrics.com content by any third-party lyrics provider is prohibited by our licensing agreement\. Sorry -->(.*?)</div>'
            match = re.search(lyrics_pattern, html_content, re.DOTALL)

            if match:
                letras = match.group(1).strip()
                letras = re.sub(r'<br\s*/?>', '\n', letras)
                letras = re.sub(r'<.*?>', '', letras)
                if letras and len(letras) > 100:
                    return letras[:3000]
    except Exception as e:
        print(f"❌ Error en AZLyrics: {e}")

    return None

# 📌 MODO CON LRC + MÚSICA (MEJORADO)
def descargar_con_lrc(track_id, calidad="flac"):
    """Descarga desde Deezer con sistema mejorado de letras"""
    try:
        # Limpiar descargas anteriores
        for f in glob.glob(f"{DOWNLOAD_DIR}/*"):
            try:
                os.remove(f)
            except:
                pass

        if not track_id.isdigit():
            return None, None, None, "Error"

        print(f"🔧 [CON LRC MEJORADO] Iniciando descarga para track: {track_id}")

        # Obtener información de la canción para búsqueda de letras
        track_info = obtener_info_cancion(track_id)
        if not track_info:
            print("❌ [CON LRC] No se pudo obtener información de la canción")
            return None, None, None, "Error"

        # BÚSQUEDA MEJORADA DE LETRAS ANTES DE DESCARGAR
        print("🔍 [LETRAS] Iniciando búsqueda profunda de letras...")
        letras_avanzadas, metodo_letras = buscar_letras_avanzado(track_info)

        # Mapear calidad a bitrate de deemix
        bitrate_map = {
            "flac": "9",
            "320": "3",
            "128": "1"
        }

        bitrate = bitrate_map.get(calidad, "9")

        # Usar deemix para descargar audio
        cmd = ["deemix", "-b", bitrate, "-p", DOWNLOAD_DIR, f"https://www.deezer.com/track/{track_id}"]
        print(f"🔧 [CON LRC] Ejecutando: {' '.join(cmd)}")

        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        stdout, stderr = process.communicate(input=ARL + "\n", timeout=120)

        print(f"📋 [CON LRC] Output: {stdout}")
        if stderr:
            print(f"⚠️ [CON LRC] Errors: {stderr}")

        # Esperar y buscar archivos descargados
        time.sleep(5)
        archivos = glob.glob(f"{DOWNLOAD_DIR}/**/*", recursive=True)
        print(f"📁 [CON LRC] Archivos encontrados: {archivos}")

        # Buscar archivo de audio
        archivo_audio = None
        calidad_real = None

        for archivo in archivos:
            if archivo.lower().endswith(".flac"):
                archivo_audio = archivo
                calidad_real = "FLAC"
                break
            elif archivo.lower().endswith(".mp3") and not archivo_audio:
                archivo_audio = archivo
                calidad_real = "MP3"

        # GESTIÓN MEJORADA DE ARCHIVOS LRC
        archivo_letras_lrc = None

        # 1. Primero buscar LRC descargado por deemix
        for archivo in archivos:
            if archivo.lower().endswith('.lrc'):
                archivo_letras_lrc = archivo
                print(f"📝 [CON LRC] Archivo LRC encontrado por deemix: {archivo_letras_lrc}")
                metodo_letras = "Deemix LRC"
                break

        # 2. Si no hay LRC de deemix pero tenemos letras de búsqueda avanzada
        if not archivo_letras_lrc and letras_avanzadas:
            print("📝 [CON LRC] Creando archivo LRC desde búsqueda avanzada...")
            titulo = track_info.get('title', 'Cancion')
            artista = track_info.get('artist', {}).get('name', 'Artista')

            # Crear nombre de archivo seguro
            safe_filename = re.sub(r'[<>:"/\\|?*]', '_', f"{artista} - {titulo}")
            archivo_letras_lrc = os.path.join(DOWNLOAD_DIR, f"{safe_filename}.lrc")

            try:
                with open(archivo_letras_lrc, 'w', encoding='utf-8') as f:
                    f.write(letras_avanzadas)
                print(f"✅ [CON LRC] Archivo LRC creado: {archivo_letras_lrc}")
            except Exception as e:
                print(f"❌ [CON LRC] Error creando LRC: {e}")
                archivo_letras_lrc = None

        # 3. Si aún no hay LRC, intentar una búsqueda final
        if not archivo_letras_lrc and track_info:
            print("🔍 [CON LRC] Último intento de búsqueda de letras...")
            letras_final, metodo_final = buscar_letras_deezer_profundo(track_id, track_info)
            if letras_final:
                titulo = track_info.get('title', 'Cancion')
                artista = track_info.get('artist', {}).get('name', 'Artista')
                safe_filename = re.sub(r'[<>:"/\\|?*]', '_', f"{artista} - {titulo}")
                archivo_letras_lrc = os.path.join(DOWNLOAD_DIR, f"{safe_filename}.lrc")

                try:
                    with open(archivo_letras_lrc, 'w', encoding='utf-8') as f:
                        f.write(letras_final)
                    print(f"✅ [CON LRC] Archivo LRC creado en último intento")
                    metodo_letras = metodo_final
                except Exception as e:
                    print(f"❌ [CON LRC] Error en último intento: {e}")
                    archivo_letras_lrc = None

        print(f"✅ [CON LRC] Resultado final - Audio: {archivo_audio}, LRC: {archivo_letras_lrc}, Método: {metodo_letras}")
        return archivo_audio, calidad_real, archivo_letras_lrc, metodo_letras

    except subprocess.TimeoutExpired:
        print("❌ [CON LRC] Timeout en la descarga")
        return None, None, None, "Error"
    except Exception as e:
        print(f"❌ Error en descarga con LRC: {e}")
        return None, None, None, "Error"

# 📌 MODO SOLO MÚSICA (SIN LRC)
def descargar_sin_lrc(track_id, calidad="320"):
    """Descarga desde Deezer sin archivos LRC"""
    try:
        # Limpiar descargas anteriores
        for f in glob.glob(f"{DOWNLOAD_DIR}/*"):
            try:
                os.remove(f)
            except:
                pass

        if not track_id.isdigit():
            return None, None, None, "Error"

        print(f"🔧 [SIN LRC] Iniciando descarga para track: {track_id}")

        # Mapear calidad a bitrate de deemix
        bitrate_map = {
            "flac": "9",
            "320": "3",
            "128": "1"
        }

        bitrate = bitrate_map.get(calidad, "3")

        # Usar deemix para descargar audio sin letras
        cmd = ["deemix", "-b", bitrate, "-p", DOWNLOAD_DIR, f"https://www.deezer.com/track/{track_id}"]
        print(f"🔧 [SIN LRC] Ejecutando: {' '.join(cmd)}")

        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        stdout, stderr = process.communicate(input=ARL + "\n", timeout=120)

        print(f"📋 [SIN LRC] Output: {stdout}")
        if stderr:
            print(f"⚠️ [SIN LRC] Errors: {stderr}")

        # Esperar y buscar archivos descargados
        time.sleep(5)
        archivos = glob.glob(f"{DOWNLOAD_DIR}/**/*", recursive=True)
        print(f"📁 [SIN LRC] Archivos encontrados: {archivos}")

        # Buscar archivo de audio
        archivo_audio = None
        calidad_real = None

        for archivo in archivos:
            if archivo.lower().endswith(".flac"):
                archivo_audio = archivo
                calidad_real = "FLAC"
                break
            elif archivo.lower().endswith(".mp3") and not archivo_audio:
                archivo_audio = archivo
                calidad_real = "MP3"

        print(f"✅ [SIN LRC] Resultado final - Audio: {archivo_audio}, Calidad: {calidad_real}")
        return archivo_audio, calidad_real, None, "Deezer Sin LRC"

    except subprocess.TimeoutExpired:
        print("❌ [SIN LRC] Timeout en la descarga")
        return None, None, None, "Error"
    except Exception as e:
        print(f"❌ Error en descarga sin LRC: {e}")
        return None, None, None, "Error"

# 📌 FUNCIONES PARA ARCHIVOS LRC
def leer_archivo_lrc(ruta_archivo):
    """Lee y formatea un archivo LRC"""
    try:
        with open(ruta_archivo, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        print(f"📖 [LRC] Archivo leído correctamente, tamaño: {len(contenido)} caracteres")
        return contenido
    except Exception as e:
        print(f"❌ Error leyendo archivo LRC: {e}")
        return None

def extraer_texto_lrc(contenido_lrc):
    """Extrae solo el texto de un archivo LRC, sin los tiempos"""
    if not contenido_lrc:
        return None

    lineas = contenido_lrc.split('\n')
    letras_texto = []

    for linea in lineas:
        linea = linea.strip()
        if not linea:
            continue

        if ']' in linea:
            partes = linea.split(']', 1)
            if len(partes) > 1:
                texto = partes[1].strip()
                if texto and not texto.startswith('[') and len(texto) > 1:
                    letras_texto.append(texto)
        elif linea and not linea.startswith('[') and len(linea) > 1:
            letras_texto.append(linea)

    resultado = '\n'.join(letras_texto) if letras_texto else None
    print(f"📝 [LRC] Texto extraído: {len(resultado) if resultado else 0} caracteres")
    return resultado

# 📌 MENÚS DE BOTONES
def menu_principal():
    keyboard = [
        [InlineKeyboardButton("🎵 Buscar Canción", callback_data="buscar_cancion")],
        [InlineKeyboardButton("👩‍🎤 Buscar Artista", callback_data="buscar_artista")],
        [InlineKeyboardButton("💿 Buscar Álbum", callback_data="buscar_album")],
        [InlineKeyboardButton("🔄 Cambiar Modo", callback_data="cambiar_modo")],
        [InlineKeyboardButton("ℹ️ Ayuda", callback_data="ayuda")]
    ]
    return InlineKeyboardMarkup(keyboard)

def menu_modo_descarga():
    keyboard = [
        [InlineKeyboardButton("🎵 Con LRC + Música", callback_data="modo_con_lrc")],
        [InlineKeyboardButton("🎵 Solo Música (Sin LRC)", callback_data="modo_sin_lrc")],
    ]
    return InlineKeyboardMarkup(keyboard)

def menu_calidad_con_lrc(track_id):
    keyboard = [
        [InlineKeyboardButton("🎵 FLAC + LRC", callback_data=f"con_lrc_flac_{track_id}")],
        [InlineKeyboardButton("🔊 MP3 320kbps + LRC", callback_data=f"con_lrc_320_{track_id}")],
        [InlineKeyboardButton("📀 MP3 128kbps + LRC", callback_data=f"con_lrc_128_{track_id}")],
        [InlineKeyboardButton("🔄 Cambiar Modo", callback_data="cambiar_modo")],
        [InlineKeyboardButton("❌ Cancelar", callback_data="volver")]
    ]
    return InlineKeyboardMarkup(keyboard)

def menu_calidad_sin_lrc(track_id):
    keyboard = [
        [InlineKeyboardButton("🎵 FLAC", callback_data=f"sin_lrc_flac_{track_id}")],
        [InlineKeyboardButton("🔊 MP3 320kbps", callback_data=f"sin_lrc_320_{track_id}")],
        [InlineKeyboardButton("📀 MP3 128kbps", callback_data=f"sin_lrc_128_{track_id}")],
        [InlineKeyboardButton("🔄 Cambiar Modo", callback_data="cambiar_modo")],
        [InlineKeyboardButton("❌ Cancelar", callback_data="volver")]
    ]
    return InlineKeyboardMarkup(keyboard)

def menu_cancelar():
    return InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancelar Búsqueda", callback_data="volver")]])

# 📌 MOSTRAR MENÚ PRINCIPAL
async def mostrar_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, text=None):
    modo_actual = context.user_data.get("modo_descarga", "con_lrc")
    modo_texto = "🎵 *Con LRC + Música*" if modo_actual == "con_lrc" else "🎵 *Solo Música (Sin LRC)*"

    if not text:
        text = f"👋 ¡Bienvenido al Bot de Descargas Deezer! 🎵\n\n{modo_texto}"

    if update.message:
        await update.message.reply_text(
            f"{text}\n\n✨ *Características activas:*\n{obtener_caracteristicas_modo(modo_actual)}",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=menu_principal()
        )
    else:
        await update.callback_query.message.reply_text(
            f"{text}\n\n✨ *Características activas:*\n{obtener_caracteristicas_modo(modo_actual)}",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=menu_principal()
        )

def obtener_caracteristicas_modo(modo):
    if modo == "con_lrc":
        return (
            "• ✅ Calidad original de Deezer\n"
            "• ✅ Formatos: FLAC, MP3 320/128kbps\n"
            "• ✅ Letras sincronizadas y texto plano\n"
            "• ✅ Metadatos completos"
        )
    else:
        return (
            "• ✅ Descarga rápida desde Deezer\n"
            "• ✅ Formatos: FLAC, MP3 320/128kbps\n"
            "• ✅ Calidad original\n"
            "• ✅ Sin archivos LRC\n"
            "• ✅ Proceso más rápido"
        )

# 📌 HANDLER DE AYUDA
async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ayuda_text = (
        "📖 *Guía de uso MEJORADA:*\n\n"
        "🎵 *Buscar Canción*: Encuentra canciones específicas\n"
        "👩‍🎤 *Buscar Artista*: Canciones populares del artista\n"
        "💿 *Buscar Álbum*: Todas las canciones de un álbum\n"
        "🔄 *Cambiar Modo*: Alternar entre modos de descarga\n\n"
        "🎧 *Modo Con LRC (Sistema MEJORADO):*\n"
        "• Calidad original de Deezer (FLAC/MP3)\n"
        "• Metadatos y portadas completos\n\n"
        "🎧 *Modo Sin LRC:*\n"
        "• Descarga rápida desde Deezer\n"
        "• Formatos FLAC/MP3 320/128kbps\n"
        "• Sin búsqueda de letras\n"
        "• Proceso más rápido"
    )

    query = update.callback_query
    await query.message.edit_text(
        ayuda_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Volver al Menú", callback_data="volver")]])
    )

# 📌 MENÚ PRINCIPAL
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "modo_descarga" not in context.user_data:
        context.user_data["modo_descarga"] = "con_lrc"

    await mostrar_menu(update, context)

# 📌 CAMBIAR MODO DE DESCARGA
async def cambiar_modo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await query.message.edit_text(
        "🔄 *Selecciona el modo de descarga:*",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=menu_modo_descarga()
    )

async def seleccionar_modo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "modo_con_lrc":
        context.user_data["modo_descarga"] = "con_lrc"
        mensaje = "✅ *Modo Con LRC (letra) activado*\n\n"
    elif data == "modo_sin_lrc":
        context.user_data["modo_descarga"] = "sin_lrc"
        mensaje = "✅ *Modo Solo Música activado*\n\nAhora usarás descargas rápidas sin búsqueda de letras."

    await query.message.edit_text(
        mensaje,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎵 Comenzar a Buscar", callback_data="volver")]])
    )

# 📌 HANDLER PARA VOLVER AL MENÚ
async def volver_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await mostrar_menu(update, context)

# 📌 HANDLER PARA MENÚ PRINCIPAL
async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "buscar_cancion":
        context.user_data["tipo_busqueda"] = "cancion"
        await query.message.edit_text(
            "🎵 *Búsqueda de Canción*\n\nEscribe el nombre de la canción que quieres buscar:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=menu_cancelar()
        )
    elif data == "buscar_artista":
        context.user_data["tipo_busqueda"] = "artista"
        await query.message.edit_text(
            "👩‍🎤 *Búsqueda de Artista*\n\nEscribe el nombre del artista que quieres buscar:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=menu_cancelar()
        )
    elif data == "buscar_album":
        context.user_data["tipo_busqueda"] = "album"
        await query.message.edit_text(
            "💿 *Búsqueda de Álbum*\n\nEscribe el nombre del álbum que quieres buscar:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=menu_cancelar()
        )
    elif data == "cambiar_modo":
        await cambiar_modo(update, context)
    elif data == "ayuda":
        await ayuda(update, context)

# 📌 PROCESAR BÚSQUEDA (SOLO TÍTULO Y ARTISTA EN BOTONES)
async def buscar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query_text = update.message.text
    user_id = update.message.from_user.id

    if "tipo_busqueda" not in context.user_data:
        await mostrar_menu(update, context)
        return

    tipo_busqueda = context.user_data["tipo_busqueda"]

    # Mostrar mensaje de búsqueda
    search_msg = await update.message.reply_text(
        f"🔍 *Buscando {query_text}...*",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=menu_cancelar()
    )

    # Realizar búsqueda según el tipo
    if tipo_busqueda == "cancion":
        resultados = buscar_cancion(query_text, limit=10)
    elif tipo_busqueda == "artista":
        resultados = buscar_artista(query_text, limit=10)
    elif tipo_busqueda == "album":
        resultados = buscar_album(query_text, limit=10)
    else:
        resultados = []

    if not resultados:
        await search_msg.edit_text(
            "❌ *No se encontraron resultados.*\n\nIntenta con otros términos de búsqueda.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Intentar de nuevo", callback_data=f"buscar_{tipo_busqueda}")]])
        )
        return

    # Mostrar solo el mensaje simple con botones que contienen título y artista
    texto = f"🎵 *Se encontraron {len(resultados)} resultados para:* `{query_text}`\n\n*Selecciona una canción:*"

    keyboard = []

    for i, resultado in enumerate(resultados, 1):
        titulo = resultado.get('title', 'Sin título')
        artista = resultado.get('artist', {}).get('name', 'Artista desconocido')

        # Crear texto del botón con solo título y artista
        texto_boton = f"🎵 {titulo} - {artista}"

        # Limitar longitud si es muy largo (máximo 64 caracteres para Telegram)
        if len(texto_boton) > 60:
            texto_boton = texto_boton[:57] + "..."

        keyboard.append([InlineKeyboardButton(
            texto_boton,
            callback_data=f"seleccionar_{resultado['id']}"
        )])

    keyboard.append([InlineKeyboardButton("🔍 Nueva Búsqueda", callback_data="volver")])

    await search_msg.edit_text(
        texto,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# 📌 ELEGIR CALIDAD DE DESCARGA
async def elegir_calidad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    track_id = data.split("_")[1]

    # Guardar track_id en el contexto
    context.user_data["track_seleccionado"] = track_id

    # Obtener información de la canción
    track_info = obtener_info_cancion(track_id)

    if track_info:
        titulo = track_info.get('title', 'Canción')
        artista = track_info.get('artist', {}).get('name', 'Artista')
        album = track_info.get('album', {}).get('title', 'Álbum')
        duracion = track_info.get('duration', 0)
        minutos = duracion // 60
        segundos = duracion % 60

        texto = f"🎵 *{titulo}*\n👩‍🎤 {artista}\n💿 {album}\n⏱️ {minutos}:{segundos:02d}\n\n"
    else:
        texto = "🎵 *Canción seleccionada*\n\n"

    modo_actual = context.user_data.get("modo_descarga", "con_lrc")

    if modo_actual == "con_lrc":
        texto += "🎧 *Selecciona la calidad de descarga (con LRC):*"
        reply_markup = menu_calidad_con_lrc(track_id)
    else:
        texto += "🎧 *Selecciona la calidad de descarga (sin LRC):*"
        reply_markup = menu_calidad_sin_lrc(track_id)

    await query.message.edit_text(
        texto,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup
    )

# 📌 PROCESAR DESCARGA
async def descargar_cancion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith(("con_lrc_flac_", "con_lrc_320_", "con_lrc_128_", "sin_lrc_flac_", "sin_lrc_320_", "sin_lrc_128_")):
        partes = data.split("_")
        modo = partes[0] + "_" + partes[1]
        calidad = partes[2]
        track_id = partes[3]

        info_cancion = obtener_info_cancion(track_id)
        nombre_cancion = info_cancion.get('title', 'Canción') if info_cancion else 'Canción'
        artista = info_cancion.get('artist', {}).get('name', 'Artista') if info_cancion else 'Artista'

        modo_texto = "Con LRC" if modo == "con_lrc" else "Sin LRC"

        download_msg = await query.message.edit_text(
            f"⏬ *Descargando en modo {modo_texto}...*\n🎵 *{nombre_cancion}*\n🎧 Calidad: {calidad.upper()}\n⏳ Esto puede tomar unos segundos...",
            parse_mode=ParseMode.MARKDOWN
        )

        if modo == "con_lrc":
            archivo_audio, calidad_real, archivo_letras_lrc, metodo_letras = descargar_con_lrc(track_id, calidad)
        else:
            archivo_audio, calidad_real, archivo_letras_lrc, metodo_letras = descargar_sin_lrc(track_id, calidad)

        if archivo_audio and os.path.exists(archivo_audio):
            file_size = os.path.getsize(archivo_audio) / (1024 * 1024)

            await download_msg.edit_text(
                f"✅ *¡Descarga completada!*\n🎵 Calidad: {calidad_real}\n💾 Tamaño: {file_size:.1f}MB\n📤 *Enviando archivos...*",
                parse_mode=ParseMode.MARKDOWN
            )

            try:
                if info_cancion:
                    titulo = info_cancion.get('title', 'Desconocido')
                    artista = info_cancion.get('artist', {}).get('name', 'Desconocido')
                    album = info_cancion.get('album', {}).get('title', 'Desconocido')
                    duracion = info_cancion.get('duration', 0)
                    minutos = duracion // 60
                    segundos = duracion % 60

                    fuente_texto = "Deezer (Con LRC)" if modo == "con_lrc" else "Deezer (Sin LRC)"
                    caption = f"🎵 **{titulo}**\n👩‍🎤 **{artista}**\n💿 {album}\n⏱️ {minutos}:{segundos:02d}\n🎧 {calidad_real} | 💾 {file_size:.1f}MB\n🔧 {fuente_texto}"
                else:
                    fuente_texto = "Deezer (Con LRC)" if modo == "con_lrc" else "Deezer (Sin LRC)"
                    caption = f"🎵 Canción descargada\n🎧 {calidad_real} | 💾 {file_size:.1f}MB\n🔧 {fuente_texto}"

                with open(archivo_audio, "rb") as audio_file:
                    await query.message.reply_audio(
                        audio_file,
                        caption=caption,
                        parse_mode=ParseMode.MARKDOWN
                    )

                if modo == "con_lrc" and archivo_letras_lrc and os.path.exists(archivo_letras_lrc):
                    lrc_size = os.path.getsize(archivo_letras_lrc) / 1024

                    contenido_lrc = leer_archivo_lrc(archivo_letras_lrc)
                    letras_preview = extraer_texto_lrc(contenido_lrc)

                    print(f"📤 [LRC] Enviando archivo LRC: {archivo_letras_lrc}")

                    with open(archivo_letras_lrc, "rb") as lrc_file:
                        await query.message.reply_document(
                            document=lrc_file,
                            filename=f"{artista} - {titulo}.lrc",
                            caption=f"📝 *Archivo LRC incluído*\n🎵 {titulo} - {artista}\n📄 Método: {metodo_letras} | 💾 {lrc_size:.1f}KB",
                            parse_mode=ParseMode.MARKDOWN
                        )

                    print("✅ [LRC] Archivo LRC enviado correctamente")

                    if letras_preview and len(letras_preview) < 1000:
                        await query.message.reply_text(
                            f"📝 *Vista previa de letras ({metodo_letras}):*\n\n{letras_preview[:800]}...",
                            parse_mode=ParseMode.MARKDOWN
                        )
                elif modo == "con_lrc":
                    print("⚠️ [LRC] No se encontró archivo LRC para enviar")
                    await query.message.reply_text(
                        f"📝 *Letras no disponibles*\n\nNo se pudieron encontrar letras para *{nombre_cancion}* después de intentar varios métodos diferentes.",
                        parse_mode=ParseMode.MARKDOWN
                    )

                try:
                    os.remove(archivo_audio)
                    if archivo_letras_lrc and os.path.exists(archivo_letras_lrc):
                        os.remove(archivo_letras_lrc)
                except:
                    pass

                await query.message.reply_text(
                    "✅ *¡Descarga completada!* ¿Qué más quieres hacer?",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=menu_principal()
                )

            except Exception as e:
                print(f"❌ Error al enviar archivos: {e}")
                await query.message.reply_text(
                    f"❌ *Error al enviar archivos:* {str(e)}",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=menu_principal()
                )
        else:
            await download_msg.edit_text(
                "❌ *Error en la descarga.*\n\nPosibles causas:\n• La canción no está disponible\n• Problemas de conexión\n• Límite de descargas\n\nIntenta con otra canción o cambia el modo de descarga.",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=menu_principal()
            )

# 📌 REGISTRAR HANDLERS
application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(seleccionar_modo, pattern="^(modo_con_lrc|modo_sin_lrc)$"))
application.add_handler(CallbackQueryHandler(menu_callback, pattern="^(buscar_cancion|buscar_artista|buscar_album|cambiar_modo|ayuda)$"))
application.add_handler(CallbackQueryHandler(volver_handler, pattern="^volver$"))
application.add_handler(CallbackQueryHandler(elegir_calidad, pattern="^seleccionar_"))
application.add_handler(CallbackQueryHandler(descargar_cancion, pattern="^(con_lrc_flac_|con_lrc_320_|con_lrc_128_|sin_lrc_flac_|sin_lrc_320_|sin_lrc_128_)"))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, buscar))

# 📌 INICIAR BOT - VERSIÓN MÍNIMA PARA RAILWAY
if __name__ == "__main__":
    print("🤖 Bot de Descargas Deezer MEJORADO iniciado...")
    print("🎵 Modos disponibles: Con LRC + Música y Solo Música (Sin LRC)")
    print("🔍 Búsqueda por: Canción, Artista, Álbum (10 resultados)")
    
    # Ejecutar el bot directamente
    print("🚀 Iniciando bot de Telegram...")
    
    # Para Railway, necesitamos mantener el proceso vivo
    # El bot se ejecutará en el hilo principal
    try:
        application.run_polling()
    except Exception as e:
        print(f"❌ Error en el bot: {e}")
