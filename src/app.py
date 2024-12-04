import io
import logging

import streamlit as st
from PIL import Image, ImageEnhance, ImageOps
from services.image_processing import remove_bg  # Importa o serviço

# Configuração de log
logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("app.log"), logging.StreamHandler()],
)


def main():
    # Configuração inicial da página do Streamlit
    st.set_page_config(page_title="Processador de Imagens", layout="wide")
    st.title("Processador de Imagens com Remoção de Fundo")
    st.subheader(
        "Envie sua imagem e ajuste os parâmetros para personalizar o resultado"
    )

    # Sidebar para os parâmetros e ações
    st.sidebar.header("Ajustes de Processamento")

    # Upload da imagem
    uploaded_file = st.sidebar.file_uploader(
        "Escolha uma imagem", type=["jpg", "png", "jpeg"]
    )

    if uploaded_file is not None:
        # Parâmetros ajustáveis na barra lateral
        clip_hist_percent = st.sidebar.slider(
            "Porcentagem de Clip do Histograma (Brilho/Contraste)",
            min_value=0.0,
            max_value=5.0,
            value=1.0,
            step=0.1,
        )
        aplicar_suavizacao = st.sidebar.checkbox("Aplicar Suavização", value=True)
        nitidez = st.sidebar.slider(
            "Ajuste de Nitidez", min_value=1.0, max_value=3.0, value=1.0, step=0.1
        )
        saturacao = st.sidebar.slider(
            "Ajuste de Saturação", min_value=0.5, max_value=2.0, value=1.0, step=0.1
        )
        aplicar_tons_cinza = st.sidebar.checkbox(
            "Converter para Tons de Cinza", value=False
        )
        fundo_verde_chroma = st.sidebar.checkbox(
            "Aplicar Fundo Verde Chroma Key", value=False
        )

        # Mostrar a imagem original e processada em colunas com proporção fixa (50/50)
        col1, col2 = st.columns([1, 1])

        # Exibe a imagem original na primeira coluna
        with col1:
            st.image(uploaded_file, caption="Imagem Original", use_container_width=True)

        # Botão para processar a imagem na barra lateral
        if st.sidebar.button("Processar Imagem"):
            try:
                with st.spinner("Processando..."):
                    # Chama a função de processamento de imagem com os parâmetros ajustados
                    result_image = remove_bg(
                        uploaded_file,
                        clip_hist_percent,
                        aplicar_suavizacao,
                        nitidez,
                        saturacao,
                    )

                    # Aplicar ajustes adicionais na imagem usando PIL
                    if isinstance(result_image, Image.Image):
                        # Converter para Tons de Cinza, se necessário
                        if aplicar_tons_cinza:
                            result_image = result_image.convert("L")

                        # Aplicar fundo verde chroma, se necessário
                        if fundo_verde_chroma:
                            # Cria uma nova imagem com fundo verde e cola a imagem sem fundo
                            background = Image.new(
                                "RGBA", result_image.size, (0, 255, 0, 255)
                            )
                            result_image = Image.alpha_composite(
                                background, result_image.convert("RGBA")
                            )

                    # Exibe a imagem processada na segunda coluna
                    with col2:
                        st.image(
                            result_image,
                            caption="Imagem Processada (Fundo Removido)",
                            use_container_width=True,
                        )

                    # Botão para baixar a imagem processada na barra lateral
                    result_buffer = io.BytesIO()
                    result_image.save(result_buffer, format="PNG")
                    st.sidebar.download_button(
                        label="Baixar Imagem Processada",
                        data=result_buffer.getvalue(),
                        file_name="imagem_processada.png",
                        mime="image/png",
                    )
            except Exception as e:
                # Registra e exibe qualquer erro ocorrido durante o processamento da imagem
                logging.error("Erro durante o processamento da imagem", exc_info=True)
                st.sidebar.error(f"Erro no processamento da imagem: {e}")


if __name__ == "__main__":
    main()
