import hashlib
import json
from http import HTTPStatus


from pydantic import BaseModel, AnyHttpUrl, ValidationError

import settings
from db.database import Session, Url as Url_model
from response import Response


class UrlCheck(BaseModel):
    url: AnyHttpUrl


class BaseResponse(BaseModel):
    status: HTTPStatus
    data: str
    content_type: str = "application/json; charset=utf-8"
    headers: dict = {}


class MainPageService:
    def __init__(self, request):
        self.request = request

    def get(self):
        context = {
            "title": "Сокращатель ссылок 3000",
        }
        data = json.dumps(context, ensure_ascii=False)
        return Response(status=HTTPStatus.OK, data=data, content_type="application/json; charset=utf-8")

    def post(self):
        try:
            req_url = UrlCheck.parse_obj(self.request.body)
        except ValidationError:
            return Response(HTTPStatus.BAD_REQUEST, data="Введен некорректный URL")

        try:
            service = CreateShortUrlService(req_url.url)
            resp = service.create_short_url()
        except ValidationError:
            return Response(HTTPStatus.BAD_REQUEST, data="Введен некорректный URL")
        except Exception:
            data = json.dumps({"Error": "Непредвиденная ошибка сервера"}, ensure_ascii=False)
            return Response(HTTPStatus.INTERNAL_SERVER_ERROR, data=data, charset="utf-8")
        return Response(status=resp.status, data=resp.data, content_type=resp.content_type)

    def get_response(self):
        if self.request.method == "GET":
            return self.get()
        elif self.request.method == "POST":
            return self.post()


class HashMaker:
    def __init__(self, url):
        self.url = url

    def generate(self):
        return hashlib.sha256(self.url.encode()).hexdigest()[:10]


class CreateShortUrlService:
    def __init__(self, url):
        self.url = url

    def create_hash(self):
        hash_maker = HashMaker(self.url)
        hash_code = hash_maker.generate()
        return hash_code

    def _save_url(self):
        with Session() as session:
            url_in_db = session.query(Url_model).filter(Url_model.url == self.url).first()
            if url_in_db:
                return url_in_db
            url = Url_model(url=self.url, short_url=self.create_hash())
            session.add(url)
            session.commit()
        return url

    def create_short_url(self) -> BaseResponse:
        url = self._save_url()
        status = HTTPStatus.CREATED
        if url:
            result = {
                "url": url.url,
                "short_url": settings.SITE_URL + "/" + url.short_url,
            }
        else:
            result = {
                "Error": "Не удалось создать короткую ссылку"
            }
            status = HTTPStatus.INTERNAL_SERVER_ERROR
        resp = BaseResponse(status=status, data=json.dumps(result, ensure_ascii=False))
        return resp


class RedirectService:
    def __init__(self, request, hash_url):
        self.request = request
        self.hash_url = hash_url

    def get(self):
        resp = self.get_url_to_redirect()
        return Response(resp.status, headers=resp.headers, data=resp.data, content_type=resp.content_type)

    def get_response(self):
        if self.request.method == "GET":
            return self.get()
        data = json.dumps({"Error": "Метод запроса не поддерживается сервером и не может быть обработан"})
        return Response(status=HTTPStatus.NOT_IMPLEMENTED, data=data)

    def get_url_to_redirect(self):
        status = HTTPStatus.FOUND
        with Session() as session:
            res = session.query(Url_model).filter(Url_model.short_url == self.hash_url).first()
        if res:
            data = {
                "url": res.url
            }
            headers = {
                "Location": res.url
            }
        else:
            status = HTTPStatus.NOT_FOUND
            data = {
                "Error": "Url адрес с такой короткой ссылкой не найден"
            }
            headers = {}
        resp = BaseResponse(status=status, data=json.dumps(data, ensure_ascii=False), headers=headers)
        return resp
