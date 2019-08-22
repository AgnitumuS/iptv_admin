from flask import session
from flask_login import UserMixin, login_user, logout_user

from app.common.provider.entry import Provider

SERVER_POSITION_SESSION_FIELD = 'server_position'


def login_user_wrap(user):
    login_user(user)
    user.set_current_server_position(0)


class ProviderUser(UserMixin, Provider):
    def logout(self):
        session.pop(SERVER_POSITION_SESSION_FIELD)
        logout_user()

    def set_current_server_position(self, pos: int):
        session[SERVER_POSITION_SESSION_FIELD] = pos

    def get_current_server(self):
        if not self.servers:
            return None

        server_settings = self.servers[session[SERVER_POSITION_SESSION_FIELD]]
        if server_settings:
            from app import servers_manager
            return servers_manager.find_or_create_server(server_settings)

        return None

    @classmethod
    def make_provider(cls, email: str, password: str, country: str):
        return cls(email=email, password=Provider.generate_password_hash(password), country=country)
