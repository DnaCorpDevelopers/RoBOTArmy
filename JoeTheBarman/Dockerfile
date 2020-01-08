FROM python:3.7 as builder

RUN mkdir /install
WORKDIR /install

COPY requirements.txt /requirements.txt

RUN pip install --upgrade pip && pip install --no-cache-dir --target=/install -r /requirements.txt

FROM python:3.7-slim-buster AS base

COPY --from=builder /install /usr/local/lib/python3.7/site-packages

RUN useradd --create-home bot
WORKDIR /home/bot

COPY commons /home/bot/commons
COPY JoeTheBarman /home/bot/JoeTheBarman

USER bot

CMD ["python", "JoeTheBarman/bot.py"]
