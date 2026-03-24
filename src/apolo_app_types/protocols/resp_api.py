"""RESPApi model

Lightweight representation of a Redis/RESP API endpoint used by the
Valkey app output processor.

Notes:
- `ApoloSecret` in this codebase is a small runtime model (a Pydantic
  model subclass) used to reference secret keys. Do not attempt to
  serialize or reveal secret values from a secret reference.

This module contains a small data model and a helper property for
generating a connection URI string. The helper intentionally avoids
including raw secret values when the password is provided as an
`ApoloSecret` instance — a placeholder is used instead.
"""

from urllib.parse import quote

from apolo_app_types.protocols.common import AbstractAppFieldType, ApoloSecret


class RESPApi(AbstractAppFieldType):
    """Model for a RESP (Redis-like) API endpoint.

    Attributes:
        scheme: URL scheme (defaults to redis://)
        host: hostname or service name
        port: TCP port number
        base_path: optional path appended to the URI
        user: optional username for credentials
        password: an ApoloSecret (typing-only); see module docstring above
    """

    scheme: str = "redis://"
    host: str
    port: int
    base_path: str = ""
    user: str = ""
    # password may be a plain string or an ApoloSecret reference; when an
    # ApoloSecret is provided we will NOT embed the secret value in the
    # generated URI (a placeholder referencing the secret key will be used).
    password: str | ApoloSecret | None = None

    @property
    def resp_uri(self) -> str:
        """Build a redis:// style URI including credentials.

        This uses the `user` and `password` fields to produce a textual
        credentials portion. If `password` is a dict-like TypedDict it will
        be formatted into the string representation by Python; ensure caller
        provides a sensible value (e.g. cast(ApoloSecret, {"name":..., "value":...})).
        """
        creds_part = ""

        # Determine password text. If password is an ApoloSecret we avoid
        # revealing the actual secret and use a small placeholder that
        # indicates which secret key would be used.
        if isinstance(self.password, ApoloSecret):
            pw_text = f"<secret:{self.password.key}>"
        elif self.password is None:
            pw_text = ""
        else:
            pw_text = str(self.password)

        # Normalize scheme to ensure it ends with '://'
        scheme = self.scheme or ""
        if not scheme.endswith("://"):
            scheme = scheme.rstrip(":/") + "://"

        if self.user or pw_text:
            # URL-encode user and password text to avoid invalid URI
            # characters in the userinfo component.
            if self.user:
                user_enc = quote(self.user, safe="")
                pw_enc = quote(pw_text, safe="") if pw_text else ""
                creds = f"{user_enc}:{pw_enc}"
            else:
                pw_enc = quote(pw_text, safe="")
                creds = f":{pw_enc}"
            creds_part = f"{creds}@"

        base = self.base_path or ""
        if base and not base.startswith("/"):
            base = "/" + base

        return f"{scheme}{creds_part}{self.host}:{self.port}{base}"
