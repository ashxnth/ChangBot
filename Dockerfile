FROM python:3

WORKDIR /chang-bot

COPY requirements.txt ./

RUN pip install -r requirements.txt

COPY . .

CMD ["python", "index.py"]