# streamautov10_public.py
# Versión pública para GitHub - Sin sistema de licencias

import obspython as obs
import threading
import time
import urllib.request
import json
import datetime
import webbrowser
import ssl
import requests

# 🔧 DISABLE SSL VERIFICATION (for self-signed certificate)
ssl._create_default_https_context = ssl._create_unverified_context

# Global variables - TODAS EN ESPAÑOL COMO ORIGINAL
ESCENA_OBJETIVO = ""
INTERVALO_CHECK = 1.0
SERVIDOR_BASE = "https://your-domain.com"  # URL genérica
SERVIDOR_SHEETS = "https://your-domain.com"  # URL genérica
USER_CODE_TWITCH = ""
USER_CODE_KICK = ""
TWITCH_USERNAME = ""
KICK_USERNAME = ""
CONFIG_SHEET_URL = ""
configuraciones_local = {}
ultima_actualizacion_config = None
CACHE_DURACION_CONFIG = 300
estado_anterior = {}
monitoreo_activo = False
stop_event = threading.Event()
procesando = False
sistema_activo = False

# Variables para detección por eventos
verificacion_pendiente = False
ultima_escena = ""
FUENTES_A_OCULTAR = []

# 🆕 DEBOUNCE TIMER VARIABLES
ultima_tecla_timestamp = 0
debounce_timer_activo = False
DEBOUNCE_DELAY = 1.5
campo_actual_editando = ""

def iniciar_timer_debounce(campo):
    global ultima_tecla_timestamp, debounce_timer_activo, campo_actual_editando
    
    campo_actual_editando = campo
    ultima_tecla_timestamp = time.time()
    
    if not debounce_timer_activo:
        debounce_timer_activo = True
        print(f"⏰ Timer started for field: {campo}")
        
        threading.Thread(target=verificar_timer_debounce, daemon=True).start()

def verificar_timer_debounce():
    global debounce_timer_activo, ultima_tecla_timestamp
    
    while debounce_timer_activo:
        tiempo_transcurrido = time.time() - ultima_tecla_timestamp
        
        if tiempo_transcurrido >= DEBOUNCE_DELAY:
            debounce_timer_activo = False
            ejecutar_validaciones_pendientes()
            break
        
        time.sleep(0.1)

def ejecutar_validaciones_pendientes():
    global campo_actual_editando
    
    print(f"✅ Executing validation for: {campo_actual_editando}")
    
    if campo_actual_editando == "user_code_twitch" and TWITCH_USERNAME:
        enviar_user_id_twitch()
    elif campo_actual_editando == "user_code_kick" and KICK_USERNAME:
        enviar_user_id_kick()
    elif campo_actual_editando == "config_sheet_url":
        obtener_configuraciones_desde_servidor()
    
    campo_actual_editando = ""

def ocultar_fuentes_juego():
    global FUENTES_A_OCULTAR
    
    if not sistema_activo:
        return
        
    try:
        escena = obs.obs_frontend_get_current_scene()
        if not escena:
            return
            
        nombre_escena = obs.obs_source_get_name(escena)
        
        if nombre_escena != ESCENA_OBJETIVO:
            escena_obj = obs.obs_scene_from_source(escena)
            items = obs.obs_scene_enum_items(escena_obj)
            
            if items:
                for item in items:
                    fuente = obs.obs_sceneitem_get_source(item)
                    if not fuente:
                        continue
                        
                    nombre_fuente = obs.obs_source_get_name(fuente)
                    tipo_fuente = obs.obs_source_get_id(fuente)
                    
                    if tipo_fuente in ["window_capture", "game_capture"]:
                        if obs.obs_sceneitem_visible(item):
                            print(f"🔴 Hiding source when leaving Game: '{nombre_fuente}'")
                            obs.obs_sceneitem_set_visible(item, False)
                            
                            if nombre_fuente not in FUENTES_A_OCULTAR:
                                FUENTES_A_OCULTAR.append(nombre_fuente)
            
                obs.sceneitem_list_release(items)
        
        obs.obs_source_release(escena)
        
    except Exception as e:
        print(f"❌ Error hiding sources: {e}")

def extraer_ejecutable(ventana_obs):
    if ventana_obs.startswith('[') and ']:' in ventana_obs:
        return ventana_obs.split(']:')[0][1:].lower()
    return ""

def extraer_ejecutable_de_fuente(ventana_fuente):
    if ':' in ventana_fuente:
        partes = ventana_fuente.split(':')
        if len(partes) >= 3:
            return partes[-1].lower()
    return ""

def obtener_lista_ventanas_obs():
    if not sistema_activo:
        return []
        
    ventanas_disponibles = []
    
    fuente_temp = None
    propiedades = None
    
    try:
        fuente_temp = obs.obs_source_create("window_capture", "temp_source", None, None)
        if not fuente_temp:
            return []
        
        propiedades = obs.obs_source_properties(fuente_temp)
        if not propiedades:
            return []
        
        prop_ventana = obs.obs_properties_get(propiedades, "window")
        if not prop_ventana:
            return []
        
        count = obs.obs_property_list_item_count(prop_ventana)
        for i in range(count):
            nombre_ventana = obs.obs_property_list_item_name(prop_ventana, i)
            ventanas_disponibles.append(nombre_ventana)
        
    except Exception as e:
        print(f"Error getting windows: {e}")
    finally:
        if propiedades:
            obs.obs_properties_destroy(propiedades)
        if fuente_temp:
            obs.obs_source_release(fuente_temp)
    
    return ventanas_disponibles

def obtener_fuentes_captura_escena():
    if not sistema_activo:
        return {}
        
    fuentes_config = {}
    
    escena = None
    items = None
    
    try:
        escena = obs.obs_frontend_get_current_scene()
        if not escena:
            return {}
        
        nombre_escena = obs.obs_source_get_name(escena)
        if nombre_escena != ESCENA_OBJETIVO:
            return {}
        
        escena_obj = obs.obs_scene_from_source(escena)
        items = obs.obs_scene_enum_items(escena_obj)
        
        if not items:
            return {}
        
        for item in items:
            fuente = obs.obs_sceneitem_get_source(item)
            if not fuente:
                continue
                
            nombre_fuente = obs.obs_source_get_name(fuente)
            tipo_fuente = obs.obs_source_get_id(fuente)
            
            if tipo_fuente in ["window_capture", "game_capture"]:
                settings = obs.obs_source_get_settings(fuente)
                if settings:
                    ventana_config = obs.obs_data_get_string(settings, "window")
                    if ventana_config:
                        ejecutable = extraer_ejecutable_de_fuente(ventana_config)
                        fuentes_config[nombre_fuente] = {
                            "item": item,
                            "ventana": ventana_config,
                            "ejecutable": ejecutable,
                            "visible_actual": obs.obs_sceneitem_visible(item)
                        }
                    obs.obs_data_release(settings)
        
    except Exception as e:
        print(f"Error getting scene sources: {e}")
    finally:
        if items:
            obs.sceneitem_list_release(items)
        if escena:
            obs.obs_source_release(escena)
    
    return fuentes_config

def verificar_y_actualizar_ventanas():
    if not sistema_activo:
        return
        
    try:
        ventanas_obs = obtener_lista_ventanas_obs()
        ejecutables_disponibles = []
        
        for ventana in ventanas_obs:
            ejecutable = extraer_ejecutable(ventana)
            if ejecutable:
                ejecutables_disponibles.append(ejecutable)
        
        fuentes_config = obtener_fuentes_captura_escena()
        
        for nombre_fuente, config in fuentes_config.items():
            ejecutable_fuente = config["ejecutable"]
            item = config["item"]
            visible_actual = config["visible_actual"]
            
            ejecutable_disponible = ejecutable_fuente in ejecutables_disponibles
            
            if ejecutable_disponible and not visible_actual:
                print(f"🔄 AUTOMATICALLY ACTIVATING: '{nombre_fuente}' - Executable: {ejecutable_fuente}")
                
                obs.obs_sceneitem_set_visible(item, True)
                
                manejar_fuente_visible(nombre_fuente)
                
            elif not ejecutable_disponible and visible_actual:
                print(f"🔴 AUTOMATICALLY HIDING: '{nombre_fuente}' - Executable not available")
                
                obs.obs_sceneitem_set_visible(item, False)
                
    except Exception as e:
        print(f"Error in automatic window verification: {e}")

def obtener_configuraciones_desde_servidor():
    global configuraciones_local, ultima_actualizacion_config
    
    try:
        if not CONFIG_SHEET_URL:
            print("❌ No Sheet URL configured")
            return {}
        
        ahora = datetime.datetime.now()
        if (ultima_actualizacion_config and 
            (ahora - ultima_actualizacion_config).total_seconds() < CACHE_DURACION_CONFIG and
            configuraciones_local):
            return configuraciones_local
        
        print(f"🔄 Getting configurations from server...")
        
        url = f"{SERVIDOR_SHEETS}/api/get_sheet_config"
        data = {
            "sheet_url": CONFIG_SHEET_URL
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode('utf-8'),
            headers=headers,
            method='POST'
        )
        
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode())
            
            if result.get('status') == 'success':
                nuevas_configuraciones = result.get('configuraciones', {})
                configuraciones_local = nuevas_configuraciones
                ultima_actualizacion_config = ahora
                
                print(f"🔍 DEBUG - Fuentes procesadas:")
                for obspuente, config in configuraciones_local.items():
                    print(f"   📝 '{obspuente}' -> Título: '{config['titulo']}', Categoría: '{config['categoria']}'")
                
                print(f"✅ Configurations obtained: {len(configuraciones_local)}")
                return configuraciones_local
            else:
                print(f"❌ Server error: {result.get('error')}")
                return {}
                
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP Error {e.code}: {e.reason}")
        return {}
    except Exception as e:
        print(f"❌ Error getting configurations: {e}")
        return {}

def enviar_user_id_twitch():
    global USER_CODE_TWITCH, TWITCH_USERNAME, SERVIDOR_BASE
    
    if not USER_CODE_TWITCH or not TWITCH_USERNAME:
        print("❌ Missing user code or Twitch username")
        return False
    
    try:
        url = f"{SERVIDOR_BASE}/api/twitch/set_user_id"
        data = {
            "user_code": USER_CODE_TWITCH,
            "username": TWITCH_USERNAME
        }
        
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "OBS-Plugin/1.0"
        }
        
        json_data = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(
            url,
            data=json_data,
            headers=headers,
            method='POST'
        )
        
        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                response_data = response.read().decode()
                result = json.loads(response_data)
                
                if result.get('status') == 'success':
                    print(f"✅ Twitch user verified: {result.get('username')}")
                    return True
                else:
                    print(f"❌ Server error: {result.get('error')}")
                    return False
                    
        except urllib.error.HTTPError as e:
            print(f"❌ HTTP Error {e.code}: {e.reason}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending user_id to server: {e}")
        return False

def enviar_user_id_kick():
    global USER_CODE_KICK, KICK_USERNAME, SERVIDOR_SHEETS
    
    if not USER_CODE_KICK:
        print("❌ Missing Kick user code")
        return False
    
    try:
        url = f"{SERVIDOR_SHEETS}/api/set_user_id"
        data = {
            "user_code": USER_CODE_KICK,
            "username": KICK_USERNAME
        }
        
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "OBS-Plugin/1.0"
        }
        
        json_data = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(
            url,
            data=json_data,
            headers=headers,
            method='POST'
        )
        
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                response_data = response.read().decode()
                result = json.loads(response_data)
                
                if result.get('status') == 'success':
                    username_server = result.get('username', '')
                    user_id_server = result.get('user_id', '')
                    print(f"✅ Kick user verified: {username_server} (ID: {user_id_server})")
                    return True
                else:
                    print(f"❌ Server error: {result.get('error')}")
                    return False
                    
        except urllib.error.HTTPError as e:
            print(f"❌ HTTP Error {e.code}: {e.reason}")
            return False
            
    except Exception as e:
        print(f"❌ Error verifying Kick user: {e}")
        return False

def actualizar_stream_twitch(titulo, categoria):
    global USER_CODE_TWITCH, SERVIDOR_BASE
    
    if not USER_CODE_TWITCH:
        print("❌ No Twitch user code configured")
        return False
    
    try:
        url = f"{SERVIDOR_BASE}/api/twitch/update_stream"
        data = {
            "user_code": USER_CODE_TWITCH,
            "titulo": titulo,
            "categoria": categoria
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode('utf-8'),
            headers=headers,
            method='POST'
        )
        
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode())
            
            if result.get('status') == 'success':
                print(f"✅ Twitch stream updated: {titulo} - {categoria}")
                return True
            else:
                print(f"❌ Twitch server error: {result.get('error')}")
                return False
                
    except Exception as e:
        print(f"❌ Error updating Twitch stream: {e}")
        return False

def actualizar_stream_kick(titulo, categoria):
    global USER_CODE_KICK, SERVIDOR_SHEETS
    
    if not USER_CODE_KICK:
        print("❌ No Kick user code configured")
        return False
    
    try:
        url = f"{SERVIDOR_SHEETS}/api/update_stream"
        data = {
            "user_code": USER_CODE_KICK,
            "titulo": titulo,
            "categoria": categoria
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode('utf-8'),
            headers=headers,
            method='POST'
        )
        
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            
            if result.get('status') == 'success':
                print(f"✅ Kick stream updated: {titulo} - {categoria}")
                return True
            else:
                print(f"❌ Kick server error: {result.get('error')}")
                return False
                
    except Exception as e:
        print(f"❌ Error updating Kick stream: {e}")
        return False
        
def script_description():
    return "Automatic game detection and update system for Twitch and Kick - V10 Public Version"

def obtener_fuentes_visibilidad():
    if not sistema_activo:
        return {}
        
    escena = None
    items = None
    
    try:
        escena = obs.obs_frontend_get_current_scene()
        if not escena:
            return {}
        
        nombre_escena = obs.obs_source_get_name(escena)
        
        if nombre_escena != ESCENA_OBJETIVO:
            return {}
        
        visibilidad_actual = {}
        escena_obj = obs.obs_scene_from_source(escena)
        items = obs.obs_scene_enum_items(escena_obj)
        
        if not items:
            return {}
        
        for item in items:
            fuente = obs.obs_sceneitem_get_source(item)
            if not fuente:
                continue
            nombre_fuente = obs.obs_source_get_name(fuente)
            visible = obs.obs_sceneitem_visible(item)
            visibilidad_actual[nombre_fuente] = visible
        return visibilidad_actual
        
    except Exception as e:
        print(f"Error getting visibility: {e}")
        return {}
    finally:
        if items:
            obs.sceneitem_list_release(items)
        if escena:
            obs.obs_source_release(escena)

def actualizar_titulo_categoria(titulo, nombre_categoria):
    global procesando
    
    if procesando:
        return
    
    twitch_actualizado = False
    kick_actualizado = False
    
    if USER_CODE_TWITCH:
        twitch_actualizado = actualizar_stream_twitch(titulo, nombre_categoria)
    
    if USER_CODE_KICK:
        kick_actualizado = actualizar_stream_kick(titulo, nombre_categoria)
    
    if twitch_actualizado or kick_actualizado:
        return True
    
    print("❌ Could not update stream - Check configuration")
    return False

def manejar_fuente_visible(nombre_fuente):
    print(f"Source '{nombre_fuente}' became visible")
    
    if not configuraciones_local:
        print("🔄 Empty cache, getting configurations...")
        obtener_configuraciones_desde_servidor()
    
    config = configuraciones_local.get(nombre_fuente)
    if config:
        titulo = config["titulo"]
        categoria = config["categoria"]
        
        print(f"🎮 Updating from Sheet: {titulo} - {categoria}")
        actualizar_titulo_categoria(titulo, categoria)
    else:
        print(f"📝 No configuration in Sheet for '{nombre_fuente}'")

def verificar_cambios_completos():
    global estado_anterior
    
    if not sistema_activo:
        return
        
    try:
        print("🎯 EXECUTING COMPLETE VERIFICATION (scene change)")
        
        verificar_y_actualizar_ventanas()
        
        visibilidad_actual = obtener_fuentes_visibilidad()
        
        for nombre_fuente, visible in visibilidad_actual.items():
            if nombre_fuente not in estado_anterior:
                estado = "VISIBLE" if visible else "HIDDEN"
                print(f"🆕 NEW - Source '{nombre_fuente}' - {estado}")
                
                if visible:
                    manejar_fuente_visible(nombre_fuente)
                    
                estado_anterior[nombre_fuente] = visible
                
            elif estado_anterior[nombre_fuente] != visible:
                estado = "VISIBLE" if visible else "HIDDEN"
                print(f"🔄 CHANGE - Source '{nombre_fuente}' - {estado}")
                
                if visible:
                    manejar_fuente_visible(nombre_fuente)
                    
                estado_anterior[nombre_fuente] = visible
        
        for nombre_fuente in list(estado_anterior.keys()):
            if nombre_fuente not in visibilidad_actual:
                print(f"🗑️ REMOVED - Source '{nombre_fuente}'")
                del estado_anterior[nombre_fuente]
                
    except Exception as e:
        print(f"❌ Error in complete verification: {e}")

def manejar_evento_obs(event):
    global verificacion_pendiente
    
    if event == obs.OBS_FRONTEND_EVENT_SCENE_CHANGED:
        escena_actual = obs.obs_frontend_get_current_scene()
        if escena_actual:
            nombre_escena = obs.obs_source_get_name(escena_actual)
            obs.obs_source_release(escena_actual)
            
            print(f"🔄 Event: Scene change to '{nombre_escena}'")
            
            if nombre_escena == ESCENA_OBJETIVO:
                print("🎯 Change to Game scene - Scheduling verification...")
                verificacion_pendiente = True
            else:
                print("🚪 Leaving Game scene - Hiding sources...")
                ocultar_fuentes_juego()

def callback_verificacion():
    global verificacion_pendiente
    
    if not sistema_activo or stop_event.is_set():
        return True
    
    if verificacion_pendiente:
        verificar_cambios_completos()
        verificacion_pendiente = False
    
    return True

def conectar_twitch_boton(props, prop):
    print("🔗 Opening connection with Twitch...")
    try:
        auth_url = f"{SERVIDOR_BASE}/twitch/auth"
        webbrowser.open(auth_url)
        print("✅ Browser opened - Follow instructions to get your code")
    except Exception as e:
        print(f"❌ Error opening browser: {e}")
    return True

def conectar_kick_boton(props, prop):
    print("🔗 Opening connection with Kick...")
    try:
        auth_url = f"{SERVIDOR_SHEETS}/auth/kick"
        webbrowser.open(auth_url)
        print("✅ Browser opened - Follow instructions to get your code")
    except Exception as e:
        print(f"❌ Error opening browser: {e}")
    return True

def enviar_user_id_twitch_boton(props, prop):
    print("🔄 Verifying Twitch user...")
    if enviar_user_id_twitch():
        print("✅ Twitch user verified successfully")
    else:
        print("❌ Twitch user verification failed")
    return True

def enviar_user_id_kick_boton(props, prop):
    print("🔄 Verifying Kick user...")
    if enviar_user_id_kick():
        print("✅ Kick user verified successfully")
    else:
        print("❌ Kick user verification failed")
    return True

def on_user_code_twitch_modified(props, prop, settings):
    global USER_CODE_TWITCH
    USER_CODE_TWITCH = obs.obs_data_get_string(settings, "user_code_twitch")
    iniciar_timer_debounce("user_code_twitch")

def on_user_code_kick_modified(props, prop, settings):
    global USER_CODE_KICK
    USER_CODE_KICK = obs.obs_data_get_string(settings, "user_code_kick")
    iniciar_timer_debounce("user_code_kick")

def on_twitch_username_modified(props, prop, settings):
    global TWITCH_USERNAME
    TWITCH_USERNAME = obs.obs_data_get_string(settings, "twitch_username")
    iniciar_timer_debounce("twitch_username")

def on_kick_username_modified(props, prop, settings):
    global KICK_USERNAME
    KICK_USERNAME = obs.obs_data_get_string(settings, "kick_username")
    iniciar_timer_debounce("kick_username")

def on_config_sheet_url_modified(props, prop, settings):
    global CONFIG_SHEET_URL
    CONFIG_SHEET_URL = obs.obs_data_get_string(settings, "config_sheet_url")
    iniciar_timer_debounce("config_sheet_url")

def on_escena_modified(props, prop, settings):
    global ESCENA_OBJETIVO
    ESCENA_OBJETIVO = obs.obs_data_get_string(settings, "escena")
    iniciar_timer_debounce("escena")

def script_load(settings):
    global current_settings, sistema_activo
    global USER_CODE_TWITCH, USER_CODE_KICK, TWITCH_USERNAME, KICK_USERNAME
    global CONFIG_SHEET_URL, ESCENA_OBJETIVO, INTERVALO_CHECK
    
    current_settings = settings
    
    USER_CODE_TWITCH = obs.obs_data_get_string(settings, "user_code_twitch")
    USER_CODE_KICK = obs.obs_data_get_string(settings, "user_code_kick")
    TWITCH_USERNAME = obs.obs_data_get_string(settings, "twitch_username")
    KICK_USERNAME = obs.obs_data_get_string(settings, "kick_username")
    CONFIG_SHEET_URL = obs.obs_data_get_string(settings, "config_sheet_url")
    ESCENA_OBJETIVO = obs.obs_data_get_string(settings, "escena")
    
    sistema_activo = True
    
    print(f"🚀 UNIFIED SYSTEM STARTED - Twitch & Kick (V10 Public)")
    print(f"🎯 Scene: '{ESCENA_OBJETIVO}'")
    print(f"🔗 Twitch Server: {SERVIDOR_BASE}")
    print(f"🔗 Kick Server: {SERVIDOR_SHEETS}")
    print(f"👤 Twitch Code: {USER_CODE_TWITCH}")
    print(f"👤 Kick Code: {USER_CODE_KICK}")
    print(f"📄 Sheet URL: {CONFIG_SHEET_URL}")
    
    obs.obs_frontend_add_event_callback(manejar_evento_obs)
    print("✅ Event handler registered")
    
    obtener_configuraciones_desde_servidor()
    
    stop_event.clear()
    
    obs.timer_add(callback_verificacion, int(INTERVALO_CHECK * 1000))
    
    if USER_CODE_TWITCH and TWITCH_USERNAME:
        print("🔄 Verifying Twitch user automatically...")
        enviar_user_id_twitch()
    
    if USER_CODE_KICK and KICK_USERNAME:
        print("🔄 Verifying Kick user automatically...")
        enviar_user_id_kick()

def script_unload():
    global sistema_activo
    
    print("🔴 Stopping unified system...")
    
    sistema_activo = False
    stop_event.set()
    
    obs.timer_remove(callback_verificacion)
    
    print("✅ System stopped correctly")

def script_properties():
    props = obs.obs_properties_create()
    
    obs.obs_properties_add_text(props, "titulo", "🎮 AUTOMATIC TWITCH & KICK SYSTEM V10 PUBLIC", obs.OBS_TEXT_INFO)
    
    obs.obs_properties_add_text(props, "paso1_twitch", "🔴 STEP 1: Configure your Twitch account", obs.OBS_TEXT_INFO)
    obs.obs_properties_add_button(props, "conectar_twitch", "🔗 1. Connect with Twitch", conectar_twitch_boton)
    
    twitch_user_prop = obs.obs_properties_add_text(props, "twitch_username", "👤 2. Your Twitch Username:", obs.OBS_TEXT_DEFAULT)
    obs.obs_property_set_modified_callback(twitch_user_prop, on_twitch_username_modified)
    
    twitch_code_prop = obs.obs_properties_add_text(props, "user_code_twitch", "🔑 3. Paste your Twitch code here:", obs.OBS_TEXT_DEFAULT)
    obs.obs_property_set_modified_callback(twitch_code_prop, on_user_code_twitch_modified)
    
    obs.obs_properties_add_button(props, "enviar_user_id_twitch", "🔄 Verify User", enviar_user_id_twitch_boton)
    
    obs.obs_properties_add_text(props, "paso2_kick", "🟣 STEP 2: Configure your Kick account", obs.OBS_TEXT_INFO)
    obs.obs_properties_add_button(props, "conectar_kick", "🔗 1. Connect with Kick", conectar_kick_boton)
    
    kick_user_prop = obs.obs_properties_add_text(props, "kick_username", "👤 2. Your Kick Username:", obs.OBS_TEXT_DEFAULT)
    obs.obs_property_set_modified_callback(kick_user_prop, on_kick_username_modified)
    
    kick_code_prop = obs.obs_properties_add_text(props, "user_code_kick", "🔑 3. Paste your Kick code here:", obs.OBS_TEXT_DEFAULT)
    obs.obs_property_set_modified_callback(kick_code_prop, on_user_code_kick_modified)
    
    obs.obs_properties_add_button(props, "enviar_user_id_kick", "🔄 Verify User", enviar_user_id_kick_boton)
    
    obs.obs_properties_add_text(props, "paso3", "🎯 STEP 3: General configuration", obs.OBS_TEXT_INFO)
    
    escena_prop = obs.obs_properties_add_text(props, "escena", "📺 Scene to monitor:", obs.OBS_TEXT_DEFAULT)
    obs.obs_property_set_modified_callback(escena_prop, on_escena_modified)
    
    sheet_prop = obs.obs_properties_add_text(props, "config_sheet_url", "📊 Your Google Sheet URL:", obs.OBS_TEXT_DEFAULT)
    obs.obs_property_set_modified_callback(sheet_prop, on_config_sheet_url_modified)
    
    return props

def script_update(settings):
    global ESCENA_OBJETIVO, current_settings, CONFIG_SHEET_URL
    global USER_CODE_TWITCH, USER_CODE_KICK, TWITCH_USERNAME, KICK_USERNAME
    
    current_settings = settings
    
    USER_CODE_TWITCH = obs.obs_data_get_string(settings, "user_code_twitch")
    USER_CODE_KICK = obs.obs_data_get_string(settings, "user_code_kick")
    TWITCH_USERNAME = obs.obs_data_get_string(settings, "twitch_username")
    KICK_USERNAME = obs.obs_data_get_string(settings, "kick_username")
    CONFIG_SHEET_URL = obs.obs_data_get_string(settings, "config_sheet_url")
    ESCENA_OBJETIVO = obs.obs_data_get_string(settings, "escena") 
    
    print(f"🔄 Configuration updated (validations in timer)")

def script_defaults(settings):
    obs.obs_data_set_string(settings, "escena", obs.obs_data_get_string(settings, "escena"))