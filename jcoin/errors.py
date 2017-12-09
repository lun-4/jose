
class GenericError(Exception):
    """Generic API error."""
    status_code = 500


class AccountNotFoundError(GenericError, Exception):
    """Account not found"""
    status_code = 404


class InputError(GenericError, Exception):
    """Client gave wrong input to a data type."""
    status_code = 400


class ConditionError(GenericError, Exception):
    """A condition was not satisfied."""
    status_code = 412

err_list = [GenericError, AccountNotFoundError,
            InputError, ConditionError]
