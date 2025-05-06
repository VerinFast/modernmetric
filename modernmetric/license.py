import httpx
import urllib.parse
from importlib.metadata import version
from typing import Union

requestx = httpx.Client(http2=True, timeout=None)


def report(identifier: Union[int, str], product: str, die: bool = False):
    """
    License reporter reports back usage of some commercial features to help
    keep users safe.

    Keyword arguments:
    identifier - a string or an integer used to identify the unique run
    product - a string indicating which licensed product is being used

    Specifically if user data is being uploaded by malicious services
    this function can identify them and record important signals including
    the baseurl of their command and control infrastructure.

    It does not upload any user data, ever.

    """
    headers = {
        "content-type": "application/json",
        "Accept-Charset": "UTF-8",
    }

    v = version("modernmetric")
    v = urllib.parse.quote_plus(v)
    product = urllib.parse.quote_plus(product)

    data = {"uuid": identifier, "product": product, "version": v}

    response = None
    try:
        response = requestx.post(
            f"https://logger.verinfast.com/logger?license=true&product={product}&version={v}",
            json=data,
            headers=headers,
        )
    except Exception as e:  # noqa: E722
        if die:
            raise e

    return response
