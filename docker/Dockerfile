FROM node:lts

WORKDIR /usr/src/app

# https://stackoverflow.com/questions/59732335/is-there-any-disadvantage-in-using-pythondontwritebytecode-in-docker
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

ENV PIP_BREAK_SYSTEM_PACKAGES 1

COPY . /usr/src/app
RUN npm install
RUN apt update && apt install -y python3 python3-pip
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pip install -r requirements_prod.txt

RUN mkdir -p /var/log/gunicorn

EXPOSE 8080

CMD ["gunicorn", "vzs.wsgi:application", "--bind", "0.0.0.0:8080", "--log-level", "info", "--log-file", "/var/log/gunicorn/gunicorn.log", "--access-logfile", "/var/log/gunicorn/gunicorn-access.log"]
