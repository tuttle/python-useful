import unicodedata


GUESS_ENCODINGS_SEQUENCE = 'UTF-8', 'CP1250', 'ISO-8859-2'


def guess_decode(s, fallback_method='replace'):
    for enc in GUESS_ENCODINGS_SEQUENCE:
        try:
            return s.decode(enc)
        except UnicodeDecodeError:
            pass
    return s.decode('UTF-8', fallback_method)


def strip_accents(unistr):
    """
    Return the accent-stripped str for the given unistr (unicode is required).
    """
    return unicodedata.normalize('NFKD', unistr).encode('ascii', 'ignore').decode('ascii')


def encoded_stream(stream, into='UTF-8'):
    import codecs

    if (stream.encoding or '').upper() != into.upper():
        stream = codecs.getwriter(into)(stream)

    return stream


def auto_encode_stdout_stderr(into='UTF-8'):
    """
    Call this on the top of your program to avoid the need of encoding each printed
    unicode object when the output encoding is not known such as during shell redirection.
    """
    import sys

    sys.stdout = encoded_stream(sys.stdout, into)
    sys.stderr = encoded_stream(sys.stderr, into)
