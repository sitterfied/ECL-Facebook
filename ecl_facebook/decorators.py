from functools import wraps
import cgi
import urllib

from django.http import HttpResponseRedirect

from ecl_facebook.signals import post_facebook_auth
from ecl_facebook import constants

def facebook_begin(fun):
    @wraps(fun)
    def k(request, *args, **kwargs):
        fun(request, *args, **kwargs)
        return HttpResponseRedirect(constants.FACEBOOK_DIALOG_URL)
    return k

def facebook_callback(fun):
    """
    Decorator for views that generates an Graph API access token after a user
    authorizes the application on Facebook.

    The wrapped view is given three parameters: the original `request`
    parameter, the access token (`token`), and the Facebook id of the user who
    authenticated (`id`).
    """
    @wraps(fun)
    def k(request, *args, **kwargs):
        code = request.GET.get('code', None)
        if not code:
            # XXX Incorporate better app-specific error handling here.
            return HttpResponse("'code' is a required parameter.")

        params = constants.FACEBOOK_ACCESS_TOKEN_PARAMS.copy()
        params['code'] = code
        url = "https://graph.facebook.com/oauth/access_token?" + urllib.urlencode(params)

        # Fetch the access token
        response = urllib.urlopen(url)
        data = response.read()
        attributes = cgi.parse_qs(data)
        token = attributes['access_token'][0]
        post_facebook_auth.send('ecl_facebook', token=token)
        return fun(request, token, *args, **kwargs)
    return k

