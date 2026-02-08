#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import io

# Forzar UTF-8 en Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    
#!/usr/bin/env python3
"""
Generador de Videos con Cloudinary - VERSIÓN INSTAGRAM VERTICAL
Formato 9:16 (1080x1920) con texto SIEMPRE CENTRADO
"""

import random
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import json
from datetime import datetime
import time
from dotenv import load_dotenv
load_dotenv()

try:
    import cloudinary
    import cloudinary.uploader
    TIENE_CLOUDINARY = True
except ImportError:
    TIENE_CLOUDINARY = False
    print("⚠️ Instala cloudinary: pip install cloudinary")

try:
    from moviepy.editor import (
        VideoFileClip, ImageClip, CompositeVideoClip, 
        concatenate_videoclips, AudioFileClip
    )
except ImportError as e:
    print(f"Error: No se puede importar MoviePy: {e}")
    exit(1)

try:
    import edge_tts
    import asyncio
    TIENE_EDGE_TTS = True
except ImportError:
    TIENE_EDGE_TTS = False

from gtts import gTTS
import tempfile
import os
import colorsys


class GeneradorVideoPexels:
    PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")
    EFECTOS = ['zoom_in', 'zoom_out', 'pan_left', 'pan_right', 'fade']
    IDEAS_BUSQUEDA = ["mindfulness", "yoga", "meditation", "zen", "spiritual", "hindu", "La India", "karma", "dharma", "hinduismo", "budismo"]
    
    CLOUDINARY_DEFAULTS = {
    'cloud_name': os.getenv('CLOUDINARY_CLOUD_NAME', ''),
    'api_key': os.getenv('CLOUDINARY_API_KEY', ''),
    'api_secret': os.getenv('CLOUDINARY_API_SECRET', '')
}
    
    def __init__(self, api_key=None, resolucion=(1080, 1920), json_path=None, 
                 cloudinary_cloud_name=None, cloudinary_api_key=None, cloudinary_api_secret=None):
        self.api_key = api_key or self.PEXELS_API_KEY
        # FORMATO VERTICAL INSTAGRAM (9:16)
        self.resolucion = resolucion
        self.temp_dir = tempfile.mkdtemp()
        self.json_path = json_path or "mindfulness.json"
        
        # Generar timestamp único para este video
        self.timestamp = int(time.time())
        self.fecha_legible = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Configurar Cloudinary con valores por defecto si no se proporcionan
        self.cloudinary_configured = False
        
        if TIENE_CLOUDINARY:
            # Usar credenciales proporcionadas o las por defecto
            cloud_name = cloudinary_cloud_name or self.CLOUDINARY_DEFAULTS['cloud_name']
            api_key = cloudinary_api_key or self.CLOUDINARY_DEFAULTS['api_key']
            api_secret = cloudinary_api_secret or self.CLOUDINARY_DEFAULTS['api_secret']
            
            try:
                cloudinary.config(
                    cloud_name=cloud_name,
                    api_key=api_key,
                    api_secret=api_secret,
                    secure=True
                )
                self.cloudinary_configured = True
                print("✅ Cloudinary configurado correctamente")
                print(f"   📦 Cloud Name: {cloud_name}")
                print(f"   🔑 API Key: {api_key[:4]}...{api_key[-4:]}")
                print(f"   🔐 Secret: {api_secret[:4]}...{api_secret[-4:]}")
            except Exception as e:
                print(f"❌ Error configurando Cloudinary: {e}")
                self.cloudinary_configured = False
        else:
            print("❌ Módulo 'cloudinary' no instalado")
            print("   Instala con: pip install cloudinary")
    
    def subir_a_cloudinary(self, video_path, tema):
        """Sube el video a Cloudinary SOBRESCRIBIENDO el anterior con nombre FIJO"""
        if not self.cloudinary_configured:
            print("\n⚠️ Cloudinary no está configurado - video NO subido")
            print(f"   El video está guardado localmente en: {video_path}")
            return None
        
        try:
            # Verificar que el archivo existe
            if not os.path.exists(video_path):
                print(f"❌ Error: El archivo {video_path} no existe")
                return None
            
            # NOMBRE FIJO - SIEMPRE EL MISMO (sin importar el tema)
            public_id = "video_ig"  # ← SIEMPRE el mismo nombre
            
            tamanio_mb = os.path.getsize(video_path) / 1024 / 1024
            
            print(f"\n{'='*70}")
            print(f"☁️  SUBIENDO A CLOUDINARY (NOMBRE FIJO)")
            print(f"{'='*70}")
            print(f"   📁 Archivo: {os.path.basename(video_path)}")
            print(f"   📊 Tamaño: {tamanio_mb:.2f} MB")
            print(f"   🆔 Public ID: {public_id}")
            print(f"   📂 Carpeta: mindfulness_videos")
            print(f"   🔄 Sobrescribirá CUALQUIER video anterior")
            print(f"{'='*70}\n")
            
            # Subir a Cloudinary CON SOBRESCRITURA
            response = cloudinary.uploader.upload(
                video_path,
                resource_type="video",
                folder="mindfulness_videos",
                public_id=public_id,
                overwrite=True,  # ← SOBRESCRIBIR el anterior
                invalidate=True,  # Invalidar cache del CDN
                eager=[{"format": "mp4", "quality": "auto"}],
                eager_async=False
            )
            
            print(f"\n{'='*70}")
            print(f"✅ VIDEO SUBIDO EXITOSAMENTE")
            print(f"{'='*70}")
            print(f"📍 URL: {response['secure_url']}")
            print(f"🆔 Public ID: {response['public_id']}")
            print(f"📅 Fecha: {self.fecha_legible}")
            print(f"📏 Formato: {response.get('format', 'mp4')}")
            print(f"⏱️  Duración: {response.get('duration', 'N/A')} seg")
            print(f"{'='*70}\n")
            
            # Guardar URL en JSON
            url_data = {
                "url": response['secure_url'],
                "public_id": response['public_id'],
                "tema": tema,
                "timestamp": self.timestamp,
                "fecha": self.fecha_legible,
                "formato": response.get('format', 'mp4'),
                "duracion": response.get('duration', None),
                "tamanio_mb": round(tamanio_mb, 2)
            }
            
            # Guardar solo en video_url.json (siempre el mismo archivo)
            url_file_principal = os.path.join(os.path.dirname(video_path) or '.', "video_url.json")
            with open(url_file_principal, 'w', encoding='utf-8') as f:
                json.dump(url_data, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Información guardada en: {url_file_principal}\n")
            
            return response
            
        except Exception as e:
            print(f"\n{'='*70}")
            print(f"❌ ERROR AL SUBIR A CLOUDINARY")
            print(f"{'='*70}")
            print(f"Error: {e}")
            print(f"{'='*70}\n")
            import traceback
            traceback.print_exc()
            return None
    
    def leer_mindfulness_json(self):
        """Lee mindfulness.json"""
        try:
            # Debug: mostrar rutas
            print(f"\n🔍 DEBUG - Buscando archivo JSON:")
            print(f"   Directorio actual: {os.getcwd()}")
            print(f"   Ruta del script: {os.path.dirname(os.path.abspath(__file__))}")
            print(f"   Archivo buscado: {self.json_path}")
            print(f"   Ruta absoluta: {os.path.abspath(self.json_path)}")
            print(f"   ¿Existe? {os.path.exists(self.json_path)}")
            
            # Si el archivo no existe en la ruta actual, buscar en el directorio del script
            if not os.path.exists(self.json_path):
                script_dir = os.path.dirname(os.path.abspath(__file__))
                json_path_alternativo = os.path.join(script_dir, self.json_path)
                print(f"   Intentando ruta alternativa: {json_path_alternativo}")
                if os.path.exists(json_path_alternativo):
                    self.json_path = json_path_alternativo
                    print(f"   ✓ Encontrado en: {self.json_path}")
            
            with open(self.json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            print(f"\n❌ Error: No se encuentra el archivo {self.json_path}")
            print(f"   Directorio actual: {os.getcwd()}")
            print(f"   Archivos en el directorio:")
            try:
                for archivo in os.listdir(os.getcwd()):
                    print(f"      - {archivo}")
            except:
                pass
            raise
        except json.JSONDecodeError:
            print(f"❌ Error: El archivo {self.json_path} no es un JSON válido")
            raise
        
        tema = data.get('tema', 'mindfulness')
        frases = data.get('frases', [])[:3]
        
        print(f"\n{'='*70}")
        print(f"📖 CONTENIDO DEL JSON")
        print(f"{'='*70}")
        print(f"✅ Tema: {tema}")
        print(f"✅ Frases encontradas: {len(frases)}")
        for i, frase in enumerate(frases, 1):
            print(f"   {i}. {frase[:60]}{'...' if len(frase) > 60 else ''}")
        print(f"{'='*70}\n")
        
        return tema, frases
    
    def buscar_imagenes_pexels(self, cantidad=5):
        """Busca imágenes en Pexels - MODO VERTICAL"""
        if not self.api_key or self.api_key == "TU_API_KEY_AQUI":
            return []
        
        idea = random.choice(self.IDEAS_BUSQUEDA)
        
        try:
            url = "https://api.pexels.com/v1/search"
            headers = {"Authorization": self.api_key}
            params = {
                "query": idea,
                "per_page": cantidad,
                "page": random.randint(1, 10),
                "orientation": "portrait"  # ← VERTICAL para Instagram
            }
            
            print(f"🔍 Buscando imágenes verticales: '{idea}'")
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code != 200:
                print(f"   ⚠️ Error API Pexels: {response.status_code}")
                return []
            
            data = response.json()
            imagenes = []
            
            if 'photos' not in data or len(data['photos']) == 0:
                print(f"   ⚠️ No se encontraron imágenes para '{idea}'")
                return []
            
            for photo in data['photos'][:cantidad]:
                try:
                    img_url = photo['src']['large2x']
                    img_response = requests.get(img_url, timeout=10)
                    if img_response.status_code == 200:
                        img = Image.open(BytesIO(img_response.content))
                        # Recortar a 9:16 centrado
                        img = self.recortar_a_vertical(img)
                        imagenes.append(img)
                except:
                    continue
            
            print(f"   ✓ {len(imagenes)} imágenes descargadas")
            return imagenes
        except Exception as e:
            print(f"   ⚠️ Error buscando imágenes: {e}")
            return []
    
    def recortar_a_vertical(self, img):
        """Recorta imagen al formato 9:16 (1080x1920) CENTRADO"""
        width, height = img.size
        target_ratio = 9 / 16  # 0.5625
        current_ratio = width / height
        
        if current_ratio > target_ratio:
            # Imagen muy ancha, recortar los lados
            new_width = int(height * target_ratio)
            left = (width - new_width) // 2
            img = img.crop((left, 0, left + new_width, height))
        else:
            # Imagen muy alta, recortar arriba/abajo
            new_height = int(width / target_ratio)
            top = (height - new_height) // 2
            img = img.crop((0, top, width, top + new_height))
        
        # Redimensionar a 1080x1920
        img = img.resize(self.resolucion, Image.LANCZOS)
        return img
    
    def buscar_videos_pexels(self, cantidad=3):
        """Busca videos en Pexels - MODO VERTICAL"""
        if not self.api_key or self.api_key == "TU_API_KEY_AQUI":
            return []
        
        idea = random.choice(self.IDEAS_BUSQUEDA)
        
        try:
            url = "https://api.pexels.com/videos/search"
            headers = {"Authorization": self.api_key}
            params = {
                "query": idea,
                "per_page": cantidad * 2,
                "page": random.randint(1, 5),
                "orientation": "portrait"  # ← VERTICAL para Instagram
            }
            
            print(f"🎥 Buscando videos verticales: '{idea}'")
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code != 200:
                print(f"   ⚠️ Error API Pexels: {response.status_code}")
                return []
            
            data = response.json()
            videos = []
            
            if 'videos' not in data:
                print(f"   ⚠️ No se encontraron videos")
                return []
            
            for video in data['videos']:
                if len(videos) >= cantidad:
                    break
                
                try:
                    if video['duration'] < 5:
                        continue
                    
                    vf = video['video_files'][0]
                    for v in video['video_files']:
                        if v['quality'] in ['hd', 'sd'] and v['height'] >= 1920:
                            vf = v
                            break
                    
                    video_url = vf['link']
                    video_response = requests.get(video_url, timeout=30)
                    if video_response.status_code == 200:
                        video_path = os.path.join(self.temp_dir, f"pexels_{len(videos)}.mp4")
                        with open(video_path, 'wb') as f:
                            f.write(video_response.content)
                        videos.append(video_path)
                except:
                    continue
            
            print(f"   ✓ {len(videos)} videos descargados")
            return videos
        except Exception as e:
            print(f"   ⚠️ Error buscando videos: {e}")
            return []
    
    def generar_paleta_colores(self, tema):
        """Genera paleta de colores"""
        return [(72, 61, 139), (218, 165, 32), (255, 248, 220)]
    
    def generar_imagen_abstracta(self, paleta):
        """Genera imagen abstracta VERTICAL"""
        img = Image.new('RGB', self.resolucion, paleta[0])
        draw = ImageDraw.Draw(img)
        for _ in range(20):
            x = random.randint(0, self.resolucion[0])
            y = random.randint(0, self.resolucion[1])
            r = random.randint(50, 300)
            draw.ellipse([x-r, y-r, x+r, y+r], fill=random.choice(paleta))
        return img
    
    def aplicar_efecto(self, clip, efecto, dur):
        """Aplica efectos al clip"""
        try:
            if efecto == 'zoom_in':
                return clip.resize(lambda t: 1 + 0.3 * (t / dur))
            elif efecto == 'zoom_out':
                return clip.resize(lambda t: 1.3 - 0.3 * (t / dur))
        except:
            pass
        return clip.fadein(0.3).fadeout(0.3)
    
    def generar_audio(self, texto):
        """Genera audio con TTS - VOZ GRAVE Y PAUSADA"""
        audio_path = os.path.join(self.temp_dir, f"audio_{hash(texto)}.mp3")
        
        if TIENE_EDGE_TTS:
            try:
                import sys
                if sys.platform == 'win32':
                    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
                
                async def gen():
                    # Voz más grave (-25Hz) y más lenta (-15%)
                    comm = edge_tts.Communicate(
                        texto, 
                        "es-ES-AlvaroNeural",
                        rate="-15%",   # Más lenta
                        pitch="-25Hz"  # Más grave
                    )
                    await comm.save(audio_path)
                
                asyncio.run(gen())
                audio_clip = AudioFileClip(audio_path)
                dur = audio_clip.duration
                audio_clip.close()
                return audio_path, dur
            except:
                pass
        
        tts = gTTS(text=texto, lang='es', slow=True)
        tts.save(audio_path)
        audio_clip = AudioFileClip(audio_path)
        dur = audio_clip.duration
        audio_clip.close()
        return audio_path, dur
    
    def crear_texto(self, frase, duracion):
        """
        Crea texto SIEMPRE CENTRADO PERFECTAMENTE
        Optimizado para formato vertical de Instagram
        """
        # Cargar fuente con tamaño ajustado para vertical
        try:
            # Tamaño de fuente más grande para pantalla vertical
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
        except:
            try:
                font = ImageFont.truetype("arial.ttf", 60)
            except:
                font = ImageFont.load_default()
        
        # Crear imagen transparente del tamaño del video
        img = Image.new('RGBA', self.resolucion, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # MÁRGENES LATERALES - Más pequeños para formato vertical
        margen_lateral = 100  # 50px a cada lado (total 100px)
        max_width = self.resolucion[0] - margen_lateral
        
        # DIVIDIR TEXTO EN LÍNEAS
        palabras = frase.split()
        lines = []
        current_line = ""
        
        for palabra in palabras:
            test_line = (current_line + " " + palabra).strip()
            
            # Medir el ancho del texto
            bbox = draw.textbbox((0, 0), test_line, font=font)
            test_width = bbox[2] - bbox[0]
            
            if test_width <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                    current_line = palabra
                else:
                    # Si una sola palabra es muy larga, la dividimos
                    lines.append(palabra)
                    current_line = ""
        
        if current_line:
            lines.append(current_line)
        
        if not lines:
            lines = [frase]
        
        # CALCULAR POSICIÓN CENTRADA
        center_x = self.resolucion[0] // 2  # Centro horizontal (540)
        center_y = self.resolucion[1] // 2  # Centro vertical (960)
        
        # Altura de línea con espacio entre líneas
        line_height = 80
        
        # Calcular altura total del bloque de texto
        total_height = len(lines) * line_height
        
        # Calcular posición Y inicial para centrar el bloque completo
        start_y = center_y - (total_height // 2) + (line_height // 2)
        
        # DIBUJAR CADA LÍNEA CENTRADA
        for i, line in enumerate(lines):
            y_pos = start_y + (i * line_height)
            
            # SOMBRA para mejor legibilidad
            shadow_offset = 3
            for dx in range(-shadow_offset, shadow_offset + 1):
                for dy in range(-shadow_offset, shadow_offset + 1):
                    if dx != 0 or dy != 0:
                        draw.text(
                            (center_x + dx, y_pos + dy),
                            line,
                            font=font,
                            fill=(0, 0, 0, 200),  # Sombra negra semi-transparente
                            anchor='mm'  # CENTRADO: Middle-Middle
                        )
            
            # TEXTO PRINCIPAL CENTRADO
            draw.text(
                (center_x, y_pos),
                line,
                font=font,
                fill=(255, 255, 255, 255),  # Blanco sólido
                anchor='mm'  # CENTRADO: Middle-Middle
            )
        
        # Guardar imagen temporal
        path = os.path.join(self.temp_dir, f"txt_{hash(frase)}.png")
        img.save(path)
        
        # Crear clip de video con la imagen de texto
        clip = ImageClip(path, duration=duracion, transparent=True)
        
        # Aplicar fade in/out suave
        return [clip.fadein(0.3).fadeout(0.3)]
    
    def ajustar_video_vertical(self, video_clip, duracion):
        """Ajusta un video al formato vertical 9:16 recortando y centrando"""
        w, h = video_clip.size
        target_ratio = 9 / 16
        current_ratio = w / h
        
        if current_ratio > target_ratio:
            # Video muy ancho, recortar los lados
            new_width = int(h * target_ratio)
            x_offset = (w - new_width) // 2
            video_clip = video_clip.crop(x1=x_offset, width=new_width)
        else:
            # Video muy alto, recortar arriba/abajo
            new_height = int(w / target_ratio)
            y_offset = (h - new_height) // 2
            video_clip = video_clip.crop(y1=y_offset, height=new_height)
        
        # Redimensionar a 1080x1920
        video_clip = video_clip.resize(self.resolucion)
        
        # Ajustar duración
        if video_clip.duration > duracion:
            video_clip = video_clip.subclip(0, duracion)
        else:
            video_clip = video_clip.loop(duration=duracion)
        
        return video_clip
    
    def generar_video(self, archivo_salida=None, usar_videos=True, usar_imagenes=True):
        """Genera video VERTICAL para Instagram con texto SIEMPRE CENTRADO"""
        print(f"\n{'='*70}")
        print(f"🎬 GENERANDO VIDEO VERTICAL PARA INSTAGRAM - {self.fecha_legible}")
        print(f"📱 Formato: {self.resolucion[0]}x{self.resolucion[1]} (9:16)")
        print(f"{'='*70}\n")
        
        tema, frases = self.leer_mindfulness_json()
        
        if len(frases) < 3:
            raise ValueError("❌ Error: Se necesitan al menos 3 frases en el JSON")
        
        # Nombre único para el archivo
        if archivo_salida is None:
            tema_limpio = tema.lower().replace(" ", "_").replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")[:20]
            archivo_salida = f"video_{tema_limpio}_{self.fecha_legible}.mp4"
        
        print(f"📁 Archivo de salida: {archivo_salida}\n")
        
        paleta = self.generar_paleta_colores(tema)
        
        # ========== INTRO ==========
        txt_intro = f"Tres frases sobre {tema}"
        print(f"🎙️ Generando audio intro...")
        audio_path, dur = self.generar_audio(txt_intro)
        audio_clip = AudioFileClip(audio_path)
        
        img = self.generar_imagen_abstracta(paleta) if not usar_imagenes else \
              (self.buscar_imagenes_pexels(1) or [self.generar_imagen_abstracta(paleta)])[0]
        
        img_path = os.path.join(self.temp_dir, "intro.jpg")
        img.save(img_path)
        
        img_clip = ImageClip(img_path, duration=dur)
        img_clip = self.aplicar_efecto(img_clip, random.choice(self.EFECTOS), dur)
        txt_clips = self.crear_texto(txt_intro, dur)
        
        seg_intro = CompositeVideoClip([img_clip] + txt_clips).set_audio(audio_clip)
        segmentos = [seg_intro]
        
        # ========== OBTENER CONTENIDO VISUAL ==========
        clips_visuales = []
        
        if usar_videos:
            videos = self.buscar_videos_pexels(3)
            for vp in videos:
                try:
                    clips_visuales.append(('video', VideoFileClip(vp)))
                except:
                    pass
        
        # Completar con imágenes
        while len(clips_visuales) < 3:
            if usar_imagenes:
                imgs = self.buscar_imagenes_pexels(1)
                img = imgs[0] if imgs else self.generar_imagen_abstracta(paleta)
            else:
                img = self.generar_imagen_abstracta(paleta)
            clips_visuales.append(('imagen', img))
        
        clips_visuales = clips_visuales[:3]
        
        # ========== PROCESAR FRASES ==========
        for i, (frase, (tipo, contenido)) in enumerate(zip(frases, clips_visuales), 1):
            print(f"\n📝 Segmento {i}/3: {frase[:50]}...")
            
            audio_path, dur = self.generar_audio(frase)
            audio_clip = AudioFileClip(audio_path)
            
            if tipo == 'video':
                video_clip = contenido
                # Ajustar al formato vertical
                video_clip = self.ajustar_video_vertical(video_clip, dur)
                clip_fondo = video_clip
            else:
                img = contenido
                img_path = os.path.join(self.temp_dir, f"img{i}.jpg")
                img.save(img_path)
                img_clip = ImageClip(img_path, duration=dur)
                img_clip = self.aplicar_efecto(img_clip, random.choice(self.EFECTOS), dur)
                clip_fondo = img_clip
            
            txt_clips = self.crear_texto(frase, dur)
            seg = CompositeVideoClip([clip_fondo] + txt_clips).set_audio(audio_clip)
            segmentos.append(seg)
        
        # ========== UNIR Y EXPORTAR ==========
        print("\n🎞️ Uniendo segmentos...")
        video_final = concatenate_videoclips(segmentos, method="compose")
        
        print(f"\n💾 Exportando video vertical...")
        video_final.write_videofile(
            archivo_salida,
            fps=30,  # 30 FPS para Instagram
            codec='libx264',
            audio_codec='aac',
            preset='medium',
            bitrate='5000k',  # Mejor calidad
            verbose=False,
            logger=None
        )
        
        video_final.close()
        for seg in segmentos:
            try:
                seg.close()
            except:
                pass
        
        print(f"\n{'='*70}")
        print(f"✅ VIDEO VERTICAL GENERADO EXITOSAMENTE")
        print(f"{'='*70}")
        print(f"📁 Archivo: {archivo_salida}")
        print(f"📊 Tamaño: {os.path.getsize(archivo_salida) / 1024 / 1024:.2f} MB")
        print(f"📱 Formato: {self.resolucion[0]}x{self.resolucion[1]} (9:16 Instagram)")
        print(f"{'='*70}\n")
        
        # SUBIR A CLOUDINARY CON NOMBRE FIJO
        cloudinary_response = self.subir_a_cloudinary(archivo_salida, tema)
        
        return archivo_salida, cloudinary_response


if __name__ == "__main__":
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description='Generador de videos verticales de mindfulness para Instagram')
    parser.add_argument('--cloudinary-name', default='dbqisdwxn', help='Nombre de la cuenta de Cloudinary')
    parser.add_argument('--cloudinary-key', default='595556985437699', help='API Key de Cloudinary')
    parser.add_argument('--cloudinary-secret', default='IQOcViq2OMa1Oe-M_CTFSgP0ogg', help='API Secret de Cloudinary')
    parser.add_argument('--pexels-key', default=None, help='API Key de Pexels')
    parser.add_argument('-o', '--output', default=None, help='Nombre del archivo de salida')
    parser.add_argument('--json', default='mindfulness.json', help='Archivo JSON con el tema y frases')
    parser.add_argument('--solo-imagenes', action='store_true', help='Usar solo imágenes')
    parser.add_argument('--solo-videos', action='store_true', help='Usar solo videos')
    
    args = parser.parse_args()
    
    try:
        print(f"\n{'='*70}")
        print(f"🚀 INICIANDO GENERADOR DE VIDEOS VERTICAL PARA INSTAGRAM")
        print(f"{'='*70}\n")
        
        gen = GeneradorVideoPexels(
            api_key=args.pexels_key,
            resolucion=(1080, 1920),  # FORMATO VERTICAL FORZADO
            json_path=args.json,
            cloudinary_cloud_name=args.cloudinary_name,
            cloudinary_api_key=args.cloudinary_key,
            cloudinary_api_secret=args.cloudinary_secret
        )
        
        gen.generar_video(
            archivo_salida=args.output,
            usar_videos=not args.solo_imagenes,
            usar_imagenes=not args.solo_videos
        )
        
        print(f"\n{'='*70}")
        print(f"🎉 PROCESO COMPLETADO")
        print(f"📱 Video optimizado para Instagram Stories/Reels")
        print(f"{'='*70}\n")
        
    except Exception as e:
        print(f"\n{'='*70}")
        print(f"❌ ERROR CRÍTICO")
        print(f"{'='*70}")
        print(f"{e}")
        print(f"{'='*70}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)