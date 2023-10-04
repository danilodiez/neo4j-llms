FROM python:3.10.9

WORKDIR /app

COPY . /app


RUN pip install --upgrade pip 
RUN pip install --no-cache-dir -r requirements.txt

CMD [ "uvicorn", "main:app", "--reload", "--host", "0.0.0.0" ]

