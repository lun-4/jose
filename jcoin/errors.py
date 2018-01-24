
class GenericError(Exception):
    """Generic API error."""
    status_code = 500


class TransferError(GenericError, Exception):
    """Generic transfer error"""
    pass


class AccountNotFoundError(TransferError):
    """Account not found"""
    status_code = 404


class InputError(TransferError):
    """Client gave wrong input to a data type."""
    status_code = 400


class ConditionError(TransferError):
    """A condition was not satisfied."""
    status_code = 412


err_list = [GenericError, TransferError, AccountNotFoundError,
            InputError, ConditionError]
