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
    return unicodedata.normalize('NFKD', unistr).encode('ascii', 'ignore')
