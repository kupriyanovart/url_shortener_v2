import application
import server
import settings
from services import MainPageService, RedirectService

app = application.WSGIApp()


@app.route(r"/", methods=["GET", "POST"])
def index(request):
    service = MainPageService(request=request)
    response = service.get_response()
    return response


@app.route(r"^/(?P<hash_url>\w{10})$")
def redirect(request, hash_url):
    service = RedirectService(request=request, hash_url=hash_url)
    response = service.get_response()
    return response


def make_server(server_address, application):
    serv = server.Server(server_address, application)
    return serv


if __name__ == "__main__":
    serv = make_server(server_address=settings.SERVER_ADDRESS, application=app)
    serv.serve_forever()
