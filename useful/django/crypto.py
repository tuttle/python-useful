
from django import VERSION
from django.utils.crypto import salted_hmac, constant_time_compare

# Get rid off warnings in Django 3
if VERSION[0] >= 2:
    from django.utils.encoding import smart_str as smart_text
else:
    # @RemoveFromDjangoVersion2
    from django.utils.encoding import smart_text


class SecretTokenGenerator(object):
    """
    Utility for protecting the strings (usually) against unauthorized change.
    First call make_token on the protectable and send the result token to
    the wild together with the protectable.
    When it returns, the positive result of check_token tells you the
    protectable was most likely really generated by us.
    Get inspiration on how to make this protection stronger from
    django.contrib.auth.tokens.PasswordResetTokenGenerator
    """
    def make_token(self, protectable):
        p = smart_text(protectable)
        return salted_hmac(self.__class__.__name__, p).hexdigest()[::-2]

    def check_token(self, protectable, token):
        return constant_time_compare(token, self.make_token(protectable))
