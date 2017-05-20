FROM alpine:latest

RUN apk add --update py-pip
RUN apk add --update libjpeg jpeg-dev

COPY requirements.txt /usr/src/app/
RUN pip install --no-cache-dir -r /usr/src/app/requirements.txt

COPY index.py /usr/src/app/
COPY static/ /usr/src/app/static/
COPU templates/ /usr/src/app/templates/

EXPOSE 5000

CMD ["python", "/usr/src/app/index.py"]

ENV AZURE_API_KEY aa6229c87b254d4cb31aba602e8c6a5f
