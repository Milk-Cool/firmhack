from mitmproxy import http
import firmhack


dict_config = firmhack.get_config()
config = firmhack.dict_to_obj_config(dict_config)


def request(flow: http.HTTPFlow) -> None:
    for address in config.addresses:
        if flow.request.url == address.address or flow.request.url == address.address + "/" or flow.request.url + "/" == address.address:
            file = open(address.file)
            flow.response = http.Response.make(
                200,
                file.read(),
                address.headers
            )
            file.close()
