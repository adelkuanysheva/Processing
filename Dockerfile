FROM ubuntu:18.04

LABEL maintainer="adelkuanysheva7@gmail.com"

RUN apt-get update -y && \
    apt-get install -y python3 python3-pip

COPY ./requirements.txt /Processing/requirements.txt

WORKDIR /Processing
RUN pip3 install -r requirements.txt
COPY . /Processing

ENTRYPOINT [ "python3" ]
CMD [ "app.py" ]