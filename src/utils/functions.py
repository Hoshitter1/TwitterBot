from typing import List


def calc_page(resource_num: int, request_limit_num: int):
    """

    Args:
        resource_num:
        request_limit_num:

    Returns:

    """
    return int(resource_num / request_limit_num + 1)


def parse_target_users(text_file: str) -> List[str]:
    f = open(text_file)
    return f.read().splitlines()
