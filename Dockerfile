FROM alpine:latest

RUN apk add --update build-base python-dev py-pip jpeg-dev zlib-dev
ENV LIBRARY_PATH=/lib:/usr/lib

COPY requirements.txt /usr/src/app/
RUN pip install --no-cache-dir -r /usr/src/app/requirements.txt

COPY index.py /usr/src/app/
COPY static/ /usr/src/app/static/
COPY templates/ /usr/src/app/templates/

EXPOSE 5000

CMD ["python", "/usr/src/app/index.py"]

ENV AZURE_API_KEY aa6229c87b254d4cb31aba602e8c6a5f
