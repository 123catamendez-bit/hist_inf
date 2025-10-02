import os
import streamlit as st
import base64
from openai import OpenAI
import openai
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
if 'enhanced_image' not in st.session_state:
    st.session_state.enhanced_image = None

def encode_image_to_base64(image_path):
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except FileNotFoundError:
        return None

# --- Interfaz ---
st.set_page_config(page_title='Tablero libre')
st.title('✨ Tablero Inteligente: de tu boceto a una obra mágica ✨')

with st.sidebar:
    st.subheader("🖌️ Acerca de la app")
    st.markdown("Dibuja lo que quieras y la IA intentará **describirlo, mejorarlo** y hasta crear una historia infantil a partir de ello. 🌟")

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
os.environ['OPENAI_API_KEY'] = ke
api_key = os.environ['OPENAI_API_KEY']
client = OpenAI(api_key=api_key) if api_key else None

# --- Botón principal ---
if canvas_result.image_data is not None and api_key and st.button("🔮 Analiza y mejora mi dibujo"):
    with st.spinner("✨ Interpretando tu boceto..."):
        # Guardar la imagen
        input_numpy_array = np.array(canvas_result.image_data)
        input_image = Image.fromarray(input_numpy_array.astype('uint8')).convert('RGBA')
        input_image.save('img.png')

        # Codificar la imagen
        base64_image = encode_image_to_base64("img.png")
        st.session_state.base64_image = base64_image

        # --- Paso 1: Descripción ---
        try:
            prompt_text = "Describe brevemente en español el siguiente dibujo como si fueras un ilustrador creativo para niños."
            response = openai.chat.completions.create(
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
                max_tokens=300,
            )

            full_response = response.choices[0].message.content
            st.session_state.full_response = full_response
            st.session_state.analysis_done = True

            st.success("✅ ¡Análisis completado!")
            st.subheader("📋 Descripción mágica")
            st.write(full_response)

        except Exception as e:
            st.error(f"Ocurrió un error al analizar la imagen: {e}")

        # --- Paso 2: Generar versión mejorada ---
        try:
            with st.spinner("🎨 Mejorando tu dibujo..."):
                enhanced = client.images.generate(
                    model="gpt-image-1",
                    prompt=f"Mejora este boceto: {st.session_state.full_response}. Hazlo colorido, con estilo infantil, simple y alegre.",
                    size="512x512"
                )
                enhanced_url = enhanced.data[0].url
                st.session_state.enhanced_image = enhanced_url

                st.subheader("🌟 Versión mejorada")
                st.image(enhanced_url, caption="Tu dibujo mejorado por IA")
        except Exception as e:
            st.error(f"No se pudo generar la versión mejorada: {e}")

# --- Funcionalidad extra: historia ---
if st.session_state.analysis_done:
    st.divider()
    st.subheader("📚 ¿Quieres una historia mágica?")
    if st.button("✨ Crear historia infantil"):
        with st.spinner("📖 Escribiendo historia..."):
            story_prompt = f"Basándote en esta descripción: '{st.session_state.full_response}', crea una historia infantil breve, mágica y entretenida, en español."
            story_response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": story_prompt}],
                max_tokens=500,
            )
            st.markdown("**📖 Tu historia:**")
            st.write(story_response.choices[0].message.content)

# --- Mensaje si falta API key ---
if not api_key:
    st.warning("⚠️ Por favor ingresa tu API key para usar la aplicación.")
