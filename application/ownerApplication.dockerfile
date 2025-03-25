FROM python:3

RUN mkdir -p /opt/src/application
WORKDIR /opt/src/application

COPY ownerApplication.py ./application.py
COPY configuration.py ./configuration.py
COPY models.py ./models.py
COPY rolecheck.py ./rolecheck.py
COPY requirements.txt ./requirements.txt

RUN pip install -r ./requirements.txt

ENTRYPOINT ["python", "./application.py"]
