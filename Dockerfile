FROM python:3.9
RUN pip install pipenv
RUN mkdir /code
WORKDIR /code
COPY Pipfile* /code/
RUN pipenv install --system --deploy --ignore-pipfile
COPY . .
CMD ["python", "url_shortener"]