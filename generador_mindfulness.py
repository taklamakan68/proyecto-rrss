
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import io

# Forzar UTF-8 en Windows - DEBE IR ANTES DE CUALQUIER PRINT
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

#!/usr/bin/env python3
"""
Generador de Frases de Mindfulness con Groq API (100% GRATIS)
Genera frases nuevas cada 5 minutos y las guarda en un JSON

API Key gratuita: https://console.groq.com/
- 30 requests por minuto
- 6,000 tokens por minuto
- Completamente GRATIS para siempre
"""

import json
import time
import os
from datetime import datetime
import requests
from dotenv import load_dotenv
load_dotenv()  # Cargar variables de .env


class GeneradorMindfulness:
    """
    Genera frases de mindfulness usando Groq API (LLaMA 3.3 70B - GRATIS)
    """
    
    # Obtén tu API key GRATIS en: https://console.groq.com/
    # Solo necesitas una cuenta de Google/GitHub
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")    
    # Temas para generar frases (se elige uno aleatorio cada vez)
    TEMAS = [
        # Mindfulness y Meditación
        "Meditación y respiración consciente",
        "Atención plena en el momento presente",
        "Mindfulness en la vida cotidiana",
        "Meditación guiada y visualización",
        "Respiración pranayama y energía vital",
        
        # Ayurveda
        "Ayurveda y equilibrio de doshas",
        "Alimentación ayurvédica consciente",
        "Rutinas diarias según Ayurveda (Dinacharya)",
        "Los cinco elementos y su equilibrio",
        "Plantas medicinales ayurvédicas",
        "Masaje ayurvédico y autocuidado",
        
        # Neoespiritualidad y Bienestar
        "Chakras y energía interior",
        "Ley de atracción y manifestación",
        "Gratitud y abundancia",
        "Sanación energética y reiki",
        "Cristales y piedras sanadoras",
        "Luna llena y rituales de liberación",
        "Afirmaciones positivas y reprogramación mental",
        "Conexión con el universo",
        
        # Hinduismo y Filosofía
        "Karma y dharma en la vida diaria",
        "Los Vedas y sabiduría ancestral",
        "Bhagavad Gita y enseñanzas espirituales",
        "Moksha y liberación del alma",
        "Yoga como filosofía de vida",
        "Samsara y el ciclo de renacimiento",
        
        # Dioses Hindúes
        "Shiva: transformación y destrucción creativa",
        "Ganesha: remoción de obstáculos",
        "Lakshmi: abundancia y prosperidad",
        "Saraswati: sabiduría y conocimiento",
        "Krishna: amor divino y devoción",
        "Durga: fuerza interior y protección",
        "Hanuman: devoción y servicio desinteresado",
        "Vishnu: preservación y equilibrio",
        "Kali: transformación radical y renacimiento",
        "Brahma: creación y manifestación",
        
        # Prácticas Espirituales
        "Mantras sagrados y su poder",
        "Puja y rituales de devoción",
        "Japa mala y meditación con cuentas",
        "Kirtan y canto devocional",
        "Bhakti yoga: el camino del amor",
        "Karma yoga: acción desinteresada",
        "Jnana yoga: conocimiento y discernimiento",
        
        # Conceptos Espirituales
        "Ahimsa: no violencia y compasión",
        "Satya: verdad y autenticidad",
        "Santosha: contentamiento interior",
        "Tapas: disciplina espiritual",
        "Svadhyaya: autoconocimiento",
        "Namaste: honrar lo divino en todos"
    ]
    
    def __init__(self, api_key=None, archivo_json="mindfulness.json", intervalo_minutos=5):
        """
        Inicializa el generador
        
        Args:
            api_key (str): API key de Groq (gratis en console.groq.com)
            archivo_json (str): Nombre del archivo JSON a generar
            intervalo_minutos (int): Minutos entre cada generación
        """
        self.api_key = api_key or self.GROQ_API_KEY
        
        # Ruta por defecto (compatible con Linux y Windows)
        ruta_base = os.path.dirname(os.path.abspath(__file__)) or "."
        
        # Si archivo_json es solo un nombre (sin ruta), añadir la ruta base
        if not os.path.dirname(archivo_json):
            self.archivo_json = os.path.join(ruta_base, archivo_json)
        else:
            self.archivo_json = archivo_json
        
        # Crear directorio si no existe
        os.makedirs(os.path.dirname(self.archivo_json), exist_ok=True)
        
        self.intervalo_segundos = intervalo_minutos * 60
        
        if not self.api_key or self.api_key == "TU_API_KEY_AQUI":
            print("\n⚠️  IMPORTANTE: Obtén tu API key GRATUITA de Groq")
            print("   1. Ve a https://console.groq.com/")
            print("   2. Regístrate con Google/GitHub (GRATIS)")
            print("   3. Ve a 'API Keys' y crea una nueva")
            print("   4. Cópiala y pégala en el script o pásala como parámetro\n")
            raise ValueError("API key de Groq requerida")
    
    def generar_frases_groq(self, num_frases=10):
        """
        Genera frases de mindfulness usando Groq API basadas en un tema aleatorio
        
        Args:
            num_frases (int): Número de frases a generar
            
        Returns:
            tuple: (tema_elegido, lista_de_frases)
        """
        # Seleccionar tema aleatorio
        import random
        tema = random.choice(self.TEMAS)
        
        url = "https://api.groq.com/openai/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Prompt mejorado para generar frases basadas en el tema
        prompt = f"""Genera exactamente {num_frases} frases únicas y profundas en español sobre el tema:

TEMA: {tema}

Las frases deben:
- Estar completamente relacionadas con "{tema}"
- Ser inspiradoras, profundas y originales
- Entre 12 y 25 palabras cada una
- Ser completamente DIFERENTES entre sí (no repetir ideas)
- Incluir conceptos específicos del tema
- Ser calmantes y motivadoras
- Usar vocabulario espiritual cuando sea apropiado

Responde SOLO con un JSON en este formato exacto:
{{
  "frases": [
    "frase 1 sobre {tema}",
    "frase 2 sobre {tema}",
    ...
  ]
}}

No incluyas explicaciones, solo el JSON con las {num_frases} frases."""

        payload = {
            "model": "llama-3.3-70b-versatile",  # Modelo gratis más potente de Groq
            "messages": [
                {
                    "role": "system",
                    "content": f"Eres un maestro espiritual experto en mindfulness, ayurveda, hinduismo y filosofía védica. Generas frases profundas e inspiradoras en español sobre temas específicos de espiritualidad."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 1.3,  # Más creatividad para mayor variedad
            "max_tokens": 1500,
            "response_format": {"type": "json_object"}  # Forzar respuesta JSON
        }
        
        try:
            print(f"🎯 Tema seleccionado: '{tema}'")
            print(f"🤖 Llamando a Groq API (LLaMA 3.3 70B)...")
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code != 200:
                print(f"❌ Error {response.status_code}: {response.text}")
                return None, None
            
            data = response.json()
            contenido = data['choices'][0]['message']['content']
            
            # Parsear el JSON de respuesta
            frases_data = json.loads(contenido)
            frases = frases_data.get('frases', [])
            
            print(f"✅ {len(frases)} frases generadas exitosamente sobre '{tema}'")
            return tema, frases
            
        except Exception as e:
            print(f"❌ Error generando frases: {e}")
            return None, None
    
    def guardar_json(self, tema, frases):
        """
        Guarda el tema y las frases en un archivo JSON
        
        Args:
            tema (str): Tema seleccionado
            frases (list): Lista de frases
        """
        if not frases or not tema:
            print("⚠️ No hay frases o tema para guardar")
            return
        
        data = {
            "fecha_generacion": datetime.now().isoformat(),
            "tema": tema,
            "total_frases": len(frases),
            "frases": frases
        }
        
        try:
            with open(self.archivo_json, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"💾 JSON guardado: {os.path.abspath(self.archivo_json)}")
            print(f"🎯 Tema: {tema}")
            print(f"📊 Total de frases: {len(frases)}")
            
        except Exception as e:
            print(f"❌ Error guardando JSON: {e}")
    
    def mostrar_frases(self, tema, frases):
        """
        Muestra el tema y las frases generadas en consola
        
        Args:
            tema (str): Tema seleccionado
            frases (list): Lista de frases
        """
        print("\n" + "="*70)
        print("✨ FRASES DE MINDFULNESS GENERADAS")
        print("="*70)
        print(f"\n🎯 TEMA: {tema}")
        print("="*70)
        
        for i, frase in enumerate(frases, 1):
            print(f"\n{i}. {frase}")
        
        print("\n" + "="*70 + "\n")
    
    def ejecutar_una_vez(self, num_frases=3, mostrar=True):
        """
        Ejecuta una sola generación de frases con tema aleatorio
        
        Args:
            num_frases (int): Número de frases a generar
            mostrar (bool): Mostrar frases en consola
        """
        print(f"\n{'#'*70}")
        print(f"# GENERACIÓN DE FRASES - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'#'*70}\n")
        
        tema, frases = self.generar_frases_groq(num_frases)
        
        if frases and tema:
            if mostrar:
                self.mostrar_frases(tema, frases)
            self.guardar_json(tema, frases)
            return True
        else:
            print("⚠️ No se pudieron generar frases")
            return False
    
    def ejecutar_continuamente(self, num_frases=3):
        """
        Ejecuta el generador cada X minutos indefinidamente con temas aleatorios
        
        Args:
            num_frases (int): Número de frases a generar cada vez
        """
        print(f"\n{'='*70}")
        print(f"🧘 GENERADOR CONTINUO DE MINDFULNESS (CON TEMAS ALEATORIOS)")
        print(f"{'='*70}")
        print(f"⏱️  Intervalo: {self.intervalo_segundos // 60} minutos")
        print(f"📁 Archivo: {self.archivo_json}")
        print(f"🎯 Temas disponibles: {len(self.TEMAS)}")
        print(f"🔄 Presiona Ctrl+C para detener")
        print(f"{'='*70}\n")
        
        iteracion = 1
        
        try:
            while True:
                print(f"\n🔄 ITERACIÓN #{iteracion}")
                
                if self.ejecutar_una_vez(num_frases, mostrar=True):
                    print(f"\n⏳ Esperando {self.intervalo_segundos // 60} minutos hasta la próxima generación...")
                    print(f"   (Próxima ejecución: {datetime.fromtimestamp(time.time() + self.intervalo_segundos).strftime('%H:%M:%S')})")
                else:
                    print(f"\n⚠️ Error en la generación, reintentando en 1 minuto...")
                    time.sleep(60)
                    continue
                
                # Esperar el intervalo
                time.sleep(self.intervalo_segundos)
                iteracion += 1
                
        except KeyboardInterrupt:
            print("\n\n✅ Generador detenido por el usuario")
            print(f"📊 Total de iteraciones: {iteracion}")
            print(f"📁 Último archivo: {os.path.abspath(self.archivo_json)}\n")


def generar_frases_mindfulness(api_key=None, archivo="mindfulness.json", num_frases=3):
    """
    Función simplificada para generar frases una sola vez
    
    Args:
        api_key (str): API key de Groq
        archivo (str): Nombre del archivo JSON
        num_frases (int): Número de frases a generar
    """
    generador = GeneradorMindfulness(api_key=api_key, archivo_json=archivo)
    generador.ejecutar_una_vez(num_frases)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Genera frases de mindfulness con Groq API (100% GRATIS)',
        epilog="""
IMPORTANTE: Obtén tu API key GRATUITA en https://console.groq.com/
  1. Regístrate con Google/GitHub (sin tarjeta de crédito)
  2. Ve a "API Keys" y crea una nueva
  3. Úsala con --api-key o colócala en el script

Ejemplos:
  # Generar una vez
  python %(prog)s --api-key tu_api_key_aqui
  
  # Generar 20 frases
  python %(prog)s --api-key tu_api_key_aqui -n 20
  
  # Modo continuo (cada 5 minutos)
  python %(prog)s --api-key tu_api_key_aqui --continuo
  
  # Modo continuo (cada 10 minutos)
  python %(prog)s --api-key tu_api_key_aqui --continuo -i 10
  
  # Archivo personalizado
  python %(prog)s --api-key tu_api_key_aqui -o frases.json
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--api-key', help='API key de Groq (obtener gratis en console.groq.com)')
    parser.add_argument('-o', '--output', default='mindfulness.json', help='Archivo JSON de salida')
    parser.add_argument('-n', '--num-frases', type=int, default=3, help='Número de frases a generar (default: 10)')
    parser.add_argument('-i', '--intervalo', type=int, default=5, help='Minutos entre generaciones en modo continuo (default: 5)')
    parser.add_argument('--continuo', action='store_true', help='Ejecutar continuamente cada X minutos')
    parser.add_argument('--no-mostrar', action='store_true', help='No mostrar frases en consola')
    
    args = parser.parse_args()
    
    try:
        generador = GeneradorMindfulness(
            api_key=args.api_key,
            archivo_json=args.output,
            intervalo_minutos=args.intervalo
        )
        
        if args.continuo:
            # Modo continuo
            generador.ejecutar_continuamente(num_frases=args.num_frases)
        else:
            # Una sola ejecución
            generador.ejecutar_una_vez(num_frases=args.num_frases, mostrar=not args.no_mostrar)
            
    except ValueError as e:
        print(f"\n❌ {e}")
        print("\n💡 Obtén tu API key GRATIS en: https://console.groq.com/\n")
        exit(1)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}\n")
        exit(1)