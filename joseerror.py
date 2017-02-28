#!/usr/bin/env python3

class PermissionError(Exception):
    pass

class LimitError(Exception):
    pass

class CommonError(Exception):
    pass

class JSONError(Exception):
    pass

class AioHttpError(Exception):
    pass
