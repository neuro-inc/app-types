from urllib.parse import quote

import apolo_sdk

from apolo_app_types.protocols.common import AbstractAppFieldType, ApoloSecret


class RESPApi(AbstractAppFieldType):
    scheme: str = "redis://"
    host: str
    port: int
    base_path: str = ""
    user: str = ""
    password: str | ApoloSecret | None = None

    async def _get_password_text(self, client: apolo_sdk.Client | None) -> str:
        if isinstance(self.password, ApoloSecret):
            if client is None:
                msg = "client is required to resolve ApoloSecret password"
                raise ValueError(msg)
            try:
                pw_result = await client.secrets.get(key=self.password.key)
            except apolo_sdk.ResourceNotFound as e:
                msg = f"secret not found: {self.password.key}"
                raise ValueError(msg) from e

            if pw_result is None:
                msg = f"secret value for key {self.password.key} is empty"
                raise ValueError(msg)

            if isinstance(pw_result, bytes):
                try:
                    return pw_result.decode()
                except UnicodeDecodeError:
                    return str(pw_result)
            if isinstance(pw_result, str):
                return pw_result
            return str(pw_result)

        if self.password is None:
            return ""

        return str(self.password)

    def _normalize_scheme(self) -> str:
        scheme = self.scheme or ""
        if not scheme.endswith("://"):
            scheme = scheme.rstrip(":/") + "://"
        return scheme

    async def resp_uri(self, client: apolo_sdk.Client | None = None) -> str:
        pw_text = await self._get_password_text(client)

        creds_part = ""
        if self.user or pw_text:
            if self.user:
                user_enc = quote(self.user, safe="")
                pw_enc = quote(pw_text, safe="") if pw_text else ""
                creds = f"{user_enc}:{pw_enc}"
            else:
                pw_enc = quote(pw_text, safe="")
                creds = f":{pw_enc}"
            creds_part = f"{creds}@"

        scheme = self._normalize_scheme()

        base = self.base_path or ""
        if base and not base.startswith("/"):
            base = "/" + base

        return f"{scheme}{creds_part}{self.host}:{self.port}{base}"
