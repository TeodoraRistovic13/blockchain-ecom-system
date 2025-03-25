FROM bde2020/spark-python-template:3.3.0-hadoop3.3

COPY mysql-connector-j-8.0.33.jar /app/

RUN mkdir -p /data

ENV SPARK_CLASSPATH="/app/mysql-connector-j-8.0.33.jar:${SPARK_CLASSPATH}"

WORKDIR /app

COPY main.py ./main.py
COPY product_stat.py ./product_stat.py
COPY category_stat.py ./category_stat.py
COPY requirements.txt ./requirements.txt

CMD [ "python3", "./main.py" ]

