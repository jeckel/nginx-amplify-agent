__author__ = 'Arie van Luttikhuizen'
__copyright__ = 'Copyright (C) Nginx, Inc. All rights reserved.'
__license__ = ''
__maintainer__ = 'Arie van Luttikhuizen'
__email__ = 'arie@nginx.com'


class NgxParserBaseException(Exception):
    def __init__(self, strerror, filename, lineno):
        self.args = (strerror, filename, lineno)
        self.filename = filename
        self.lineno = lineno
        self.strerror = strerror

    def __str__(self):
        return '{:s} in {:s}:{:d}'.format(*self.args)


class NgxParserSyntaxError(NgxParserBaseException):
    pass


class NgxParserDirectiveError(NgxParserBaseException):
    pass


class NgxParserDirectiveArgumentsError(NgxParserDirectiveError):
    pass


class NgxParserDirectiveContextError(NgxParserDirectiveError):
    pass
