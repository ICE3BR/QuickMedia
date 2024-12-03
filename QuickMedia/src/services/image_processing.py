import io
import logging

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageOps
from rembg import remove

# Configuração de log
logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("processing.log"), logging.StreamHandler()],
)


# Pré-Processamento de imagem
def automatic_brightness_contrast(image_np, clip_hist_percent=1):
    try:
        # Converte a imagem para escala de cinza
        gray = cv2.cvtColor(image_np, cv2.COLOR_BGR2GRAY)
        # Calcula o histograma da imagem em escala de cinza
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        accumulator = [float(hist[0])]

        # Calcula a soma acumulativa do histograma
        for index in range(1, len(hist)):
            accumulator.append(accumulator[index - 1] + float(hist[index]))

        # Calcula os limites de corte do histograma
        clip_hist_percent *= accumulator[-1] / 100.0
        clip_hist_percent /= 2.0

        # Encontra os valores mínimos e máximos de cinza para aplicar o ajuste de contraste
        min_gray = next(
            i for i in range(len(accumulator)) if accumulator[i] > clip_hist_percent
        )
        max_gray = next(
            i
            for i in range(len(accumulator) - 1, -1, -1)
            if accumulator[i] < accumulator[-1] - clip_hist_percent
        )

        # Calcula o fator de escala (alpha) e o valor de deslocamento (beta) para ajuste de contraste
        alpha = 255 / (max_gray - min_gray)
        beta = -min_gray * alpha

        # Aplica o ajuste de brilho e contraste
        return cv2.convertScaleAbs(image_np, alpha=alpha, beta=beta)

    except Exception as e:
        logging.error("Erro ao ajustar brilho e contraste", exc_info=True)
        raise ValueError("Falha ao ajustar brilho e contraste da imagem.") from e


# Removedor de Fundo com Personalizações
def remove_bg(
    image_file, clip_hist_percent=1, aplicar_suavizacao=True, nitidez=1.0, saturacao=1.0
):
    try:
        # Converte o arquivo carregado para um array de bytes e depois para uma imagem OpenCV
        image_bytes = image_file.read()
        np_image = np.frombuffer(image_bytes, np.uint8)
        image_cv = cv2.imdecode(np_image, cv2.IMREAD_COLOR)

        if image_cv is None:
            raise ValueError(
                "Falha ao carregar a imagem. Verifique se o arquivo é válido."
            )

        # Pré-processamento: Ajuste de brilho e contraste
        enhanced = automatic_brightness_contrast(image_cv, clip_hist_percent)

        # Suavização opcional usando filtro Gaussiano
        if aplicar_suavizacao:
            enhanced = cv2.GaussianBlur(enhanced, (3, 3), 0.5)

        # Converte a imagem OpenCV (BGR) para imagem PIL (RGB) para aplicar ajustes adicionais
        enhanced_pil = Image.fromarray(cv2.cvtColor(enhanced, cv2.COLOR_BGR2RGB))

        # Ajuste de Nitidez usando PIL
        sharpness_enhancer = ImageEnhance.Sharpness(enhanced_pil)
        enhanced_pil = sharpness_enhancer.enhance(nitidez)

        # Ajuste de Saturação usando PIL
        saturation_enhancer = ImageEnhance.Color(enhanced_pil)
        enhanced_pil = saturation_enhancer.enhance(saturacao)

        # Converte a imagem aprimorada de volta para bytes para remoção de fundo
        buffer = io.BytesIO()
        enhanced_pil.save(buffer, format="PNG")
        image_bytes = buffer.getvalue()

        # Remover fundo da imagem usando rembg
        output_data = remove(image_bytes)

        # Converte os bytes resultantes em uma imagem PIL
        output_image = Image.open(io.BytesIO(output_data))

        return output_image

    except Exception as e:
        logging.error("Erro ao remover o fundo da imagem", exc_info=True)
        raise ValueError("Erro ao processar a remoção de fundo da imagem.") from e


# Função para aplicar fundo verde chroma key ou converter para tons de cinza
def apply_additional_filters(image, aplicar_tons_cinza=False, fundo_verde_chroma=False):
    try:
        # Converter para Tons de Cinza, se necessário
        if aplicar_tons_cinza:
            image = image.convert("L")

        # Aplicar fundo verde chroma, se necessário
        if fundo_verde_chroma:
            # Cria uma nova imagem com fundo verde e cola a imagem sem fundo
            background = Image.new("RGBA", image.size, (0, 255, 0, 255))
            image = Image.alpha_composite(background, image.convert("RGBA"))

        return image

    except Exception as e:
        logging.error("Erro ao aplicar filtros adicionais", exc_info=True)
        raise ValueError("Erro ao aplicar filtros adicionais à imagem.") from e
