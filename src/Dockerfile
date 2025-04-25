FROM python:3.10-slim

# Copiar e configurar dependências
COPY Pipfile Pipfile.lock /app/
WORKDIR /app
RUN pip install pipenv && pipenv install --system --deploy

## Definir variáveis de ambiente
#ENV AWS_ACCESS_KEY=${AWS_ACCESS_KEY}
#ENV AWS_SECRET_KEY=${AWS_SECRET_KEY}
#ENV S3_BUCKET_NAME=${S3_BUCKET_NAME}
#ENV S3_REGION=${S3_REGION}

# Copiar o código da aplicação
COPY .. /app

# Executar o aplicativo
#CMD ["python", "appAss.py"]
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "appAss:app"]