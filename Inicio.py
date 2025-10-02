import os
import streamlit as st
import base64
import openai
from PIL import Image
import numpy as np
from streamlit_drawable_canvas import st_canvas

# --- Inicialización de session_state ---
if 'analysis_done' not in st.session_state:
    st.session_state.analysis_done = False
if 'full_response' not in st.session_state:
    st.session_state.full_response = ""
if 'base64_image' not in st.session_state:
    st.session_state.base64_image = ""
if 'creative_pack' not in st.session_state:
    st.session_state.creative_pack = ""

def encode_image_to_base64(image_path):
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except FileNotFoundError:
        return None

# --- Interfaz ---
st.set_page_config(page_title='Tablero libre')
st.title('✨ Tablero Inteligente: de tu boceto a un Pack Creativo ✨')

with st.sidebar:
    st.subheader("🖌️ Acerca de la app")
    st.markdown(
        "Dibuja lo que quieras y la IA describirá tu boceto y te devolverá un *Pack Creativo*: "
        "título, poema, paleta, actividad, prompt refinado y emojis. ¡Perfecto para jugar o inspirarte!"
    )

# --- Configuración del lienzo ---
stroke_width = st.sidebar.slider('✏️ Grosor del lápiz', 1, 30, 5)
stroke_color = st.sidebar.color_picker("🎨 Color del lápiz", "#000000")
bg_color = st.sidebar.color_picker("🌈 Fondo del lienzo", "#FFFFFF")

canvas_result = st_canvas(
    fill_color="rgba(255, 165, 0, 0.2)",
    stroke_width=stroke_width,
    stroke_color=stroke_color,
    background_color=bg_color,
    height=320,
    width=480,
    drawing_mode="freedraw",
    key="canvas",
)

# --- Clave API (texto input) ---
ke = st.text_input('🔑 Ingresa tu Clave de OpenAI', type="password")
if ke:
    openai.api_key = ke
api_key = openai.api_key if hasattr(openai, "api_key") else None

# --- Botón principal ---
if canvas_result.image_data is not None and api_key and st.button("🔮 Analiza y crea pack creativo"):
    with st.spinner("✨ Interpretando y creando arte verbal..."):
        # Guardar la imagen temporalmente
        input_numpy_array = np.array(canvas_result.image_data)
        input_image = Image.fromarray(input_numpy_array.astype('uint8')).convert('RGBA')
        input_image.save('img.png')

        # Codificar la imagen a base64 para enviarla al endpoint (si quieres contexto visual)
        base64_image = encode_image_to_base64("img.png")
        st.session_state.base64_image = base64_image

        # --- Paso 1: descripción (como ilustrador infantil) ---
        try:
            prompt_text = (
                "Describe brevemente en español el siguiente dibujo como si fueras un ilustrador "
                "creativo para niños: menciona qué se ve, sensaciones y un par de detalles visuales."
            )
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt_text},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/png;base64,{base64_image}"}
                            },
                        ],
                    }
                ],
                max_tokens=400,
            )

            full_response = response.choices[0].message.content
            st.session_state.full_response = full_response
            st.session_state.analysis_done = True

            st.success("✅ ¡Análisis completado!")
            st.subheader("📋 Descripción mágica")
            st.write(full_response)

        except Exception as e:
            st.error(f"Ocurrió un error al analizar la imagen: {e}")
            full_response = ""
            st.session_state.analysis_done = False

        # --- Paso 2: Generar el Pack Creativo (texto) ---
        if full_response:
            try:
                creative_prompt = (
                    "A partir de esta descripción (en español) crea un 'Pack Creativo' que contenga, "
                    "separado por secciones claramente etiquetadas en español, lo siguiente:\n\n"
                    "1) TITULO: Un título corto y bonito (máx. 5 palabras).\n"
                    "2) POEMA: Un poema breve de 4 líneas, apto para niños, que capture la esencia.\n"
                    "3) PALETA: Sugiere 4 colores (da nombre corto + HEX para cada uno), apropiados para colorear el dibujo.\n"
                    "4) ACTIVIDAD: Una mini-actividad/manualidad (3-5 pasos) para niños basada en el dibujo.\n"
                    "5) PROMPT_REFINADO: Un prompt en español, claro y conciso, listo para usar en un generador de imágenes (estilo 'acuarela infantil', colores vivos), para obtener una versión ilustrada.\n"
                    "6) EMOJIS: 3 emojis que acompañen la obra.\n\n"
                    f"Descripción: {full_response}\n\n"
                    "Entrega las secciones etiquetadas exactamente como 'TITULO:', 'POEMA:', 'PALETA:', 'ACTIVIDAD:', 'PROMPT_REFINADO:', 'EMOJIS:'."
                )

                creative_resp = openai.ChatCompletion.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": creative_prompt}],
                    max_tokens=600,
                )

                creative_text = creative_resp.choices[0].message.content
                st.session_state.creative_pack = creative_text

                st.divider()
                st.subheader("🎁 Pack Creativo")

                # Mostrar el pack tal cual (el assistant devolverá secciones etiquetadas)
                st.markdown(creative_text)

                # Botón para descargar el pack como .txt
                pack_bytes = creative_text.encode("utf-8")
                st.download_button(
                    label="⬇️ Descargar pack creativo (.txt)",
                    data=pack_bytes,
                    file_name="pack_creativo.txt",
                    mime="text/plain",
                )

                # Opcional: mostrar la paleta de colores si aparece (buscar HEX usando simple parse)
                # Hacemos una extracción muy básica de hex codes para mostrar visualmente
                import re
                hex_codes = re.findall(r'#(?:[0-9a-fA-F]{3}){1,2}', creative_text)
                if hex_codes:
                    st.markdown("**Paleta sugerida (vista rápida):**")
                    cols = st.columns(len(hex_codes))
                    for i, code in enumerate(hex_codes):
                        with cols[i]:
                            st.markdown(f"{code}")
                            st.markdown(f"<div style='width:80px;height:40px;background:{code};border-radius:6px;'></div>", unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Ocurrió un error generando el pack creativo: {e}")

# --- Funcionalidad extra: crear historia por separado ---
if st.session_state.analysis_done:
    st.divider()
    st.subheader("📚 ¿Quieres una historia infantil basada en la descripción?")
    if st.button("✨ Crear historia infantil"):
        with st.spinner("📖 Escribiendo historia..."):
            try:
                story_prompt = (
                    f"Basándote en esta descripción: '{st.session_state.full_response}', crea una historia infantil breve, mágica y entretenida, en español."
                )
                story_response = openai.ChatCompletion.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": story_prompt}],
                    max_tokens=400,
                )
                st.markdown("**📖 Tu historia:**")
                st.write(story_response.choices[0].message.content)
            except Exception as e:
                st.error(f"Ocurrió un error al crear la historia: {e}")

# --- Mensaje si falta API key ---
if not api_key:
    st.warning("⚠️ Por favor ingresa tu API key para usar la aplicación.")
