FROM python:3-buster

RUN apt-get update && apt-get install -y apt-transport-https ca-certificates curl gnupg2 software-properties-common && \
    curl -fsSL https://download.docker.com/linux/debian/gpg | apt-key add - && \
    add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/debian $(lsb_release -cs) stable" && \
    apt-get update && apt-get install -y docker-ce-cli

ADD requirements.txt /
RUN pip3 install -r /requirements.txt && mkdir /code

ADD . /code/

WORKDIR /code/
EXPOSE 5000
CMD ["python3", "/code/main.py"]
