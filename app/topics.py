from enum import Enum

class Topic(Enum):
    # AUTH_LOGIN_URL = "auth.login.url"
    USER_LOGIN = "user.login"


class MessageType(Enum):
    SEND_AUTH_URL = "send.auth.url"
    USER_LOGIN = "user.login"
    GENERATE_USER_INFO = "generate_user_info"