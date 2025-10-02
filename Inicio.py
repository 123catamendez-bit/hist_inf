import os
import streamlit as st
import base64
from openai import OpenAI
from PIL import Image
import numpy as np
from streamlit_drawable_canvas import st_canvas

# --- Inicialización ---
if 'analysis_done' not in st.session_state:
    st.session_state.analysis_done = False
if 'full_response' not in st.session_state:
    st.session_state.full_response = ""
if 'base64_image' not in st.session_state:
    st.session_state.base64_image = ""

def encode_image_to_base64(image_path):
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except FileNotFoundError:
        return None

# --- Interfaz ---
st.set_page_config(page_title='Tablero creativo')
st.title('✨ Tablero Inteligente: de tu boceto a un Pack Creativo ✨')

with st.sidebar:
    st.subheader("🖌️ Acerca de la app")
    st.markdown("Dibuja lo que quieras y la IA te devolverá un **Pack Creativo**: título, paleta, actividad, prompt refinado y emojis. 🌟 Perfecto para inspirarte o jugar.")

# --- Configuración del lienzo ---
stroke_width = st.sidebar.slider('✏️ Grosor del lápiz', 1, 30, 5)
stroke_color = st.sidebar.color_picker("🎨 Color del lápiz", "#000000")
bg_color = st.sidebar.color_picker("🌈 Fondo del lienzo", "#FFFFFF")

canvas_result = st_canvas(
    fill_color="rgba(255, 165, 0, 0.3)",
    stroke_width=stroke_width,
    stroke_color=stroke_color,
    background_color=bg_color,
    height=300,
    width=400,
    drawing_mode="freedraw",
    key="canvas",
)

# --- Clave API ---
ke = st.text_input('🔑 Ingresa tu Clave de OpenAI', type="password")
if ke:
    os.environ['OPENAI_API_KEY'] = ke
    client = OpenAI(api_key=ke)
else:
    client = None

# --- Botón principal ---
if canvas_result.image_data is not None and client and st.button("🔮 Analiza y crea pack creativo"):
    with st.spinner("✨ Interpretando tu boceto..."):
        # Guardar la imagen
        input_numpy_array = np.array(canvas_result.image_data)
        input_image = Image.fromarray(input_numpy_array.astype('uint8')).convert('RGBA')
        input_image.save('img.png')

        # Codificar la imagen
        base64_image = encode_image_to_base64("img.png")
        st.session_state.base64_image = base64_image

        # --- Usamos la nueva sintaxis ---
        try:
            prompt_text = """
            Eres un asistente creativo. Analiza este dibujo y devuélveme un **Pack Creativo** en formato claro:
            - ✨ Un título llamativo para el dibujo
            - 🎨 Una paleta de 3 colores que combinarían bien
            - 📝 Una mini actividad creativa que un niño podría hacer con este dibujo
            - 🌟 Un prompt refinado para inspirar a usar IA generativa
            - 😀 Algunos emojis relacionados
            Responde en español.
            """

            response = client.chat.completions.create(
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

            st.success("✅ ¡Pack creativo generado!")
            st.subheader("🎁 Pack Creativo para tu dibujo")
            st.write(full_response)

        except Exception as e:
            st.error(f"Ocurrió un error al analizar la imagen: {e}")

# --- Mensaje si falta API key ---
if not client:
    st.warning("⚠️ Por favor ingresa tu API key para usar la aplicación.")
