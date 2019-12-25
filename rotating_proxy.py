import logging
import requests

from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from random import shuffle

LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.NullHandler())

PROXY_SOURCE = 'https://www.sslproxies.org/'


# TODO: to class and get parameters for proxy_source + proxy_source_parsing_func

class DepletedProxyPoolException(Exception):
    pass


def get_proxies(link):
    response = requests.get(link)
    soup = BeautifulSoup(response.text, "lxml")
    https_proxies = filter(lambda item: "yes" in item.text,
                           soup.select("table.table tr"))
    for item in https_proxies:
        yield "{}:{}".format(item.select_one("td").text,
                             item.select_one("td:nth-of-type(2)").text)


def get_random_proxies_iter():
    proxies = list(get_proxies(PROXY_SOURCE))
    LOGGER.info('Got {} proxies to use'.format(len(proxies)))
    shuffle(proxies)
    return iter(proxies)  # iter so we can call next on it to get the next proxy


def get_proxy(session, proxies, validated=False):
    # TODO: handle StopIteration exception
    session.proxies = {'https': 'https://{}'.format(next(proxies))}
    if validated:
        while True:
            try:
                LOGGER.debug('Validating {}'.format(session.proxies['https']))
                session.get('https://httpbin.org/ip', timeout=30)
                return session
            except Exception:
                session.proxies = {'https': 'https://{}'.format(next(proxies))}


if __name__ == '__main__':
    url = input('Input url: ')
    session = requests.Session()
    ua = UserAgent()
    proxies = get_random_proxies_iter()
    while True:
        try:
            session.headers = {'User-Agent': ua.random}
            # collect a working proxy to be used to fetch a valid response
            get_proxy(session, proxies, validated=True)
            LOGGER.info('Got Proxy {}'.format(session.proxies['https']))
            break  # as soon as it fetches a valid response, it will break out of the while loop
        except StopIteration:
            # No more proxies left to try
            raise DepletedProxyPoolException('No more proxies left to try')
        except Exception as e:
            LOGGER.warning(e)
            pass  # Other errors: try again
