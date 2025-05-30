"""
This type stub file was generated by pyright.
"""

from .api import Sender

class OAuth2(Sender):
    """Genius OAuth2 authorization flow.

    Using this class you can authenticate a user,
    and get their token.

    Args:
        client_id (:obj:`str`): Client ID
        redirect_uri (:obj:`str`): Whitelisted redirect URI.
        client_secret (:obj:`str`, optional): Client secret.
        scope (:obj:`tuple` | :obj:`"all"`, optional): Token privileges.
        state (:obj:`str`, optional): Request state.
        client_only_app (:obj:`bool`, optional): `True` to use the client-only
            authorization flow, otherwise `False`.

    Raises:
        AssertionError: If neither :obj:`client_secret`, nor
            :obj:`client_only_app` is supplied.

    """

    auth_url = ...
    token_url = ...
    def __init__(
        self,
        client_id,
        redirect_uri,
        client_secret=...,
        scope=...,
        state=...,
        client_only_app=...,
    ) -> None: ...
    @property
    def url(self):  # -> str:
        """Returns the URL you redirect the user to.

        You can use this property to get a URL that when opened on the user's
        device, shows Genius's authorization page where user clicks *Agree*
        to give your app access, and then Genius redirects user back to your
        redirect URI.

        """
        ...

    def get_user_token(self, code=..., url=..., state=..., **kwargs):  # -> str | Any:
        """Gets a user token using the url or the code parameter..

        If you supply value for :obj:`code`, this method will use the value of the
        :obj:`code` parameter to request a token from Genius.

        If you use the :method`client_only_app` and supplt the redirected URL,
        it will already have the token.
        You could pass the URL to this method or parse it yourself.

        If you provide a :obj:`state` the method will also compare
        it to the initial state and will raise an exception if
        they're not equal.

        Args:
            code (:obj:`str`): 'code' parameter of redirected URL.
            url (:obj:`str`): Redirected URL (used in client-only apps)
            state (:obj:`str`): state parameter of redirected URL (only
                provide if you want to compare with initial :obj:`self.state`)
            **kwargs: keywords for the POST request.
        returns:
            :obj:`str`: User token.

        """
        ...

    def prompt_user(self):  # -> str | Any:
        """Prompts current user for authentication.

        Opens a web browser for you to log in with Genius.
        Prompts to paste the URL after logging in to parse the
        *token* URL parameter.

        returns:
            :obj:`str`: User token.

        """
        ...

    @classmethod
    def client_only_app(cls, client_id, redirect_uri, scope=..., state=...):  # -> Self:
        """Returns an OAuth2 instance for a client-only app.

        Args:
            client_id (:obj:`str`): Client ID.
            redirect_uri (:obj:`str`): Whitelisted redirect URI.
            scope (:obj:`tuple` | :obj:`"all"`, optional): Token privilages.
            state (:obj:`str`, optional): Request state.

        returns:
            :class:`OAuth2`

        """
        ...

    @classmethod
    def full_code_exchange(
        cls, client_id, redirect_uri, client_secret, scope=..., state=...
    ):  # -> Self:
        """Returns an OAuth2 instance for a full-code exchange app.

        Args:
            client_id (:obj:`str`): Client ID.
            redirect_uri (:obj:`str`): Whitelisted redirect URI.
            client_secret (:obj:`str`): Client secret.
            scope (:obj:`tuple` | :obj:`"all"`, optional): Token privilages.
            state (:obj:`str`, optional): Request state.

        returns:
            :class:`OAuth2`

        """
        ...

    def __repr__(self):  # -> str:
        ...
