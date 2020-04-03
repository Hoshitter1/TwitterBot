def calc_page(resource_num: int, request_limit_num: int):
    """

    Args:
        resource_num:
        request_limit_num:

    Returns:

    """
    return int(resource_num / request_limit_num + 1)
