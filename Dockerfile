FROM alpine:latest

ENV LIBRARY_PATH=/lib:/usr/lib
RUN apk add --update freetype freetype-dev build-base python-dev py-pip jpeg-dev zlib-dev

COPY requirements.txt /usr/src/app/
RUN pip install --no-cache-dir -r /usr/src/app/requirements.txt

COPY index.py /usr/src/app/
COPY static/ /usr/src/app/static/
COPY templates/ /usr/src/app/templates/

EXPOSE 5000

CMD ["python", "/usr/src/app/index.py"]

ENV AZURE_API_KEY aa6229c87b254d4cb31aba602e8c6a5f
