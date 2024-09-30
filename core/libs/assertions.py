from .exceptions import FyleError


def base_assert(cond, error_code, msg):
    raise FyleError(status_code=error_code, message=msg)


def assert_auth(cond, msg='UNAUTHORIZED'):
    if cond is False:
        base_assert(cond, 401, msg)


def assert_true(cond, msg='FORBIDDEN'):
    if cond is False:
        base_assert(cond, 403, msg)


def assert_valid(cond, msg='BAD_REQUEST'):
    if cond is False:
        base_assert(cond, 400, msg)


def assert_found(_obj, msg='NOT_FOUND'):
    if _obj is None:
        base_assert(_obj is not None, 404, msg)