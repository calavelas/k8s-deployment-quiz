FROM python:3.8

WORKDIR /app

COPY app.py ./

RUN pip install flask
RUN pip install kubernetes

CMD [ "python", "app.py" ]
