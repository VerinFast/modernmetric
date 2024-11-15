import httpx

requestx = httpx.Client(http2=True, timeout=None)


def report(identifier: str | int, product: str):
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
        'content-type': 'application/json',
        'Accept-Charset': 'UTF-8',
    }

    data = {
        "uuid": identifier,
        "product": product
    }

    response = requestx.post(
        f"https://logger.verinfast.com/logger?license=true&product={str(product)}",  # noqa: E501
        json=data,
        headers=headers
    )

    return response