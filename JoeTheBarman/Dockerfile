FROM python:3.7 as builder

RUN mkdir /install
WORKDIR /install

COPY requirements.txt /requirements.txt

RUN pip install --upgrade pip && pip install --no-cache-dir --target=/install -r /requirements.txt

FROM python:3.7-slim-buster AS base

COPY --from=builder /install /usr/local/lib/python3.7/site-packages

RUN mkdir /bot

COPY commons /bot/commons
COPY JoeTheBarman /bot/JoeTheBarman

CMD ["python", "/bot/JoeTheBarman/bot.py"]
