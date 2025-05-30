from apolo_app_types import AppInputs
from apolo_app_types.protocols.common import IngressHttp, Preset


class SupersetInputs(AppInputs):
    ingress_http: IngressHttp
    preset: Preset
