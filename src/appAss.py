from flask import Flask, jsonify, request
from PIL import Image
import random
from io import BytesIO
import aiohttp  # Para downloads assíncronos
import boto3
import os

app = Flask(__name__)

# Configuração do S3
AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_KEY')
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')
S3_REGION = os.getenv('S3_REGION')


s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=S3_REGION
)

# Função assíncrona para baixar imagens
async def baixar_imagem(link):
    async with aiohttp.ClientSession() as session:
        async with session.get(link) as response:
            if response.status != 200:
                raise Exception(f"Erro ao baixar a imagem: {link}")
            return Image.open(BytesIO(await response.read()))

# Função assíncrona para gerar o vision board
async def criar_vision_board(links, output_path):
    # Selecionar 37 links aleatórios
    selected_links = random.sample(links, 70)
    imagens = []

    # Baixar imagens assíncronas
    for link in selected_links:
        try:
            img = await baixar_imagem(link)
            imagens.append(img)
        except Exception as e:
            print(f"Erro ao processar a imagem: {link}, {str(e)}")

    # Criar o canvas final
    largura_final, altura_final = 1920, 1080
    vision_board = Image.new('RGB', (largura_final, altura_final), (255, 255, 255))

    # Configurar as dimensões para o grid
    num_imagens_por_linha = 7
    num_linhas = 6  # Para encaixar 42 células, mesmo usando apenas 37 imagens
    largura_img = largura_final // num_imagens_por_linha
    altura_img = altura_final // num_linhas

    x_offset, y_offset = 0, 0

    for img in imagens:
        # Redimensionar a imagem para preencher 100% do espaço da célula
        img_resized = img.resize((largura_img, altura_img))

        # Fazer crop para manter o espaço ocupado mesmo que o aspecto mude
        img_cropped = img_resized.crop((0, 0, largura_img, altura_img))
        vision_board.paste(img_cropped, (x_offset, y_offset))

        # Atualizar offsets
        x_offset += largura_img
        if x_offset >= largura_final:
            x_offset = 0
            y_offset += altura_img

    # Salvar o resultado
    vision_board.save(output_path)

# Função assíncrona para fazer upload para o S3
async def upload_to_s3(file_path, user_id):
    s3_key = f"{user_id}.jpg"  # Nome único baseado no ID do usuário
    s3_client.upload_file(file_path, S3_BUCKET_NAME, s3_key, ExtraArgs={'ContentType': 'image/jpeg'})
    s3_url = f"https://{S3_BUCKET_NAME}.s3.{S3_REGION}.amazonaws.com/{s3_key}"
    os.remove(file_path)  # Remover o arquivo local após o upload
    return s3_url

# Endpoint da API
@app.route('/generate-vision-board', methods=['POST'])
async def generate_vision_board():
    # Receber JSON com os links e o ID do usuário
    data = request.json
    links = data.get('links', [])
    user_id = data.get('user_id', 'default_user')  # Exemplo de ID do usuário

    if len(links) < 37:
        return jsonify({"error": "A lista deve conter pelo menos 37 links."}), 400

    # Gerar o vision board
    output_path = 'vision_board_temp.jpg'
    await criar_vision_board(links, output_path)

    # Fazer upload para o S3
    try:
        s3_url = await upload_to_s3(output_path, user_id)
        return jsonify({"image_url": s3_url})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000)