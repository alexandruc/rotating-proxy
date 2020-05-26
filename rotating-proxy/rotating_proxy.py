import requests

from bs4 import BeautifulSoup
from random import shuffle

class DepletedProxyPoolException(RuntimeError):
    pass
class RotatingProxy:
    DEFAULT_PROXY_SOURCE = 'https://www.sslproxies.org/'

    @staticmethod
    def _default_proxy_source_parser(link):
        response = requests.get(link)
        soup = BeautifulSoup(response.text, "lxml")
        https_proxies = filter(lambda item: "yes" in item.text,
                            soup.select("table.table tr"))
        for item in https_proxies:
            yield "{}:{}".format(item.select_one("td").text,
                                item.select_one("td:nth-of-type(2)").text)

    def __init__(self, proxy_source=DEFAULT_PROXY_SOURCE, 
                proxy_source_parser=_default_proxy_source_parser.__func__):
        """ Constructs object using a proxy source url and a proxy url parser function
        @param proxy_source url which contains proxies
        @param proxy_source_parser function to parse the url and return a list of proxies as strings
         """
        self.proxy_source = proxy_source
        self.proxy_source_parser = proxy_source_parser
        self.proxies = None

    def _get_random_proxies_iter(self):
        proxies = list(self.proxy_source_parser(self.proxy_source))
        print('Got {} proxies to use'.format(len(proxies)))
        shuffle(proxies)
        return iter(proxies)  # iter so we can call next on it to get the next proxy

    def get_proxy(self, validate=False):
        if not self.proxies:
            self.proxies = self._get_random_proxies_iter()

        try:
            proxy = next(self.proxies)
            if validate:
                session = requests.Session()
                while True:
                    try:
                        session.proxies = {'https': 'https://{}'.format(proxy)}
                        print('Validating {}'.format(session.proxies['https']))
                        session.get('https://httpbin.org/ip', timeout=30)
                        return proxy
                    except Exception:
                        proxy = next(self.proxies)
        except StopIteration as _:
            raise DepletedProxyPoolException('Ran out of proxies to rotate')

if __name__ == '__main__':
    rotating_proxy = RotatingProxy()
    while True:
        try:
            print('Collecting proxy...')
            proxy = rotating_proxy.get_proxy(validate=True)
            print('Got Proxy {}'.format(proxy))
            break  # as soon as it fetches a valid response, it will break out of the while loop
        except StopIteration:
            # No more proxies left to try
            raise DepletedProxyPoolException('No more proxies left to try')
        except Exception as e:
            print(e)
            pass  # Other errors: try again
