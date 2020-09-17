FROM python:3.6

EXPOSE 9000

WORKDIR /zid

RUN apt-get update \
    && apt-get install -y python3-dev libffi-dev libxslt-dev libxml2-dev gcc musl-dev g++ \
    && apt-get install -y  ca-certificates wget

RUN curl -L#o wk.tar.xz https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.4/wkhtmltox-0.12.4_linux-generic-amd64.tar.xz \
    && tar xf wk.tar.xz \
    && cp wkhtmltox/bin/wkhtmltopdf /usr/bin \
    && cp wkhtmltox/bin/wkhtmltoimage /usr/bin \
    && rm wk.tar.xz \
    && rm -r wkhtmltox

ADD ./requirements ./requirements
RUN pip install -r requirements

ADD . /zid
ENTRYPOINT ["./run.sh"]
CMD ["web"]
