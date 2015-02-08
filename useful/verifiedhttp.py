import httplib
import socket
import urllib2

# Python 2.6 required for the ssl module.
import ssl  # @UnresolvedImport

# Based on http://www.muchtooscrawled.com/2010/03/https-certificate-verification-in-python-with-urllib2/     @IgnorePep8

# Example usage:
# response = urlopen('https://api-3t.sandbox.paypal.com/nvp',
#    '/path/to/VeriSign-Class3_Public_Primary_Certification_Authority_G2.pem',
#    'PayPal').read()


class VerifiedHTTPSConnection(httplib.HTTPSConnection):
    CA_FILE_PATH = None
    REQUIRED_ORGANIZATION_PATTERN = None

    def match_organization(self, cert):
        if self.REQUIRED_ORGANIZATION_PATTERN is None:
            return True

        for rdn in cert['subject']:
            for k, v in rdn:
                if k == 'organizationName':
                    if self.REQUIRED_ORGANIZATION_PATTERN in v:
                        return True

        return False

    def connect(self):
        # overrides the version in httplib so that we do
        #    certificate verification
        sock = socket.create_connection((self.host, self.port), self.timeout)
        if self._tunnel_host:
            self.sock = sock
            self._tunnel()

        # wrap the socket using verification with the root
        #    certs in trusted_root_certs
        self.sock = ssl.wrap_socket(sock,
                                    self.key_file,
                                    self.cert_file,
                                    cert_reqs=ssl.CERT_REQUIRED,
                                    ca_certs=self.CA_FILE_PATH)
        cert = self.sock.getpeercert()
        if not self.match_organization(cert):
            raise urllib2.URLError("Server cert issued for wrong organization")


# wraps https connections with ssl certificate verification
class VerifiedHTTPSHandler(urllib2.HTTPSHandler):
    def __init__(self, connection_class=VerifiedHTTPSConnection):
        self.specialized_conn_class = connection_class
        urllib2.HTTPSHandler.__init__(self)

    def https_open(self, req):
        return self.do_open(self.specialized_conn_class, req)


def urlopen(url, ca_file_path, org_name_pattern=None, data=None):
    """
    urllib2.urlopen extended to verify whether the HTTPS the server certificate
    was issued by the given CA. The CA certificate file path must
    be provided.
    If the org_name_pattern is given, the organizationName of the server
    certificate is searched for the substring.
    """
    # Patches the class to set the required info.
    VerifiedHTTPSConnection.CA_FILE_PATH = ca_file_path
    VerifiedHTTPSConnection.REQUIRED_ORGANIZATION_PATTERN = org_name_pattern
    https_handler = VerifiedHTTPSHandler()
    url_opener = urllib2.build_opener(https_handler)
    return url_opener.open(url, data)
