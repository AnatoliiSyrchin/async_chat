
import os
import logging
from sqlalchemy.orm import Session, Mapped, DeclarativeBase, mapped_column, relationship
from sqlalchemy import create_engine, String, select, ForeignKey
from datetime import datetime

import logs.log_configs.server_log_config

logger = logging.getLogger('app.server')


class ServerStorage:

    class Base(DeclarativeBase):
        pass

    class AllUsers(Base):
        __tablename__ = 'all_users'

        id: Mapped[int] = mapped_column(primary_key=True)
        username: Mapped[str] = mapped_column(String(30), unique=True)
        password_hash: Mapped[str]
        public_key: Mapped[int] = mapped_column(default=0)
        last_login: Mapped[datetime]

        active_user: Mapped["ActiveUsers"] = relationship(back_populates="user")
        history_user: Mapped["LoginHistory"] = relationship(back_populates="user")
        event_user: Mapped["UsersEventsHistory"] = relationship(back_populates="user")
        # users_contact_user: Mapped["UsersContacts"] = relationship(back_populates="user")
        users_contacts: Mapped["UsersContacts"] = relationship(back_populates="user")

        def __repr__(self):
            return f'User {self.id} {self.username} {self.last_login}'

    class ActiveUsers(Base):
        __tablename__ = 'active_users'

        id: Mapped[int] = mapped_column(primary_key=True)
        user_id: Mapped[int] = mapped_column(ForeignKey('all_users.id'), unique=True)
        ip_address: Mapped[str] = mapped_column(String(45))
        port: Mapped[int]
        login_time: Mapped[datetime]

        user: Mapped["AllUsers"] = relationship(back_populates="active_user")

    class LoginHistory(Base):
        __tablename__ = 'login_history'

        id: Mapped[int] = mapped_column(primary_key=True)
        user_id: Mapped[int] = mapped_column(ForeignKey('all_users.id'))
        ip_address: Mapped[str] = mapped_column(String(45))
        port: Mapped[int]
        login_time: Mapped[datetime]

        user: Mapped["AllUsers"] = relationship(back_populates="history_user")

    class UsersContacts(Base):
        __tablename__ = 'users_contacts'

        id: Mapped[int] = mapped_column(primary_key=True)
        user_id: Mapped[int] = mapped_column(ForeignKey('all_users.id'))
        contact_id: Mapped[int]

        user: Mapped["AllUsers"] = relationship(back_populates="users_contacts")
    
    class UsersEventsHistory(Base):
        __tablename__ = 'users_events_history'

        id: Mapped[int] = mapped_column(primary_key=True)
        user_id: Mapped[int] = mapped_column(ForeignKey('all_users.id'))
        sent: Mapped[int] = mapped_column(default=0)
        received: Mapped[int] = mapped_column(default=0)

        user: Mapped["AllUsers"] = relationship(back_populates="event_user")

    def __init__(self, path, prefix=''):

        self.engine = create_engine(f'sqlite:///{path}', echo=False, pool_recycle=3600, connect_args={'check_same_thread': False})
        self.Base.metadata.create_all(self.engine)

        with Session(self.engine) as self.session:
            self.session.query(self.ActiveUsers).delete()
            self.session.commit()

    def add_user(self, username, password_hash):
        register_time = datetime.now()
        user = self.session.scalar(select(self.AllUsers).where(self.AllUsers.username == username))
        if user:
            return user
        else:
            user = self.AllUsers(
                username=username,
                last_login=register_time,
                password_hash=password_hash,
            )
            self.session.add(user)
            self.session.commit()
            events_history_user = self.UsersEventsHistory(user_id=user.id)
            self.session.add(events_history_user)
            self.session.commit()
            return True

    def user_login(self, username, ip_address, port, public_key):
        login_time = datetime.now()
        user = self.session.scalar(select(self.AllUsers).where(self.AllUsers.username == username))

        if user:
            user.last_login = login_time
            user.public_key = public_key
        else:
            raise ValueError('User not registered')

        active_user = self.ActiveUsers(user_id=user.id, ip_address=ip_address, port=port, login_time=login_time)
        history_user = self.LoginHistory(user_id=user.id, ip_address=ip_address, port=port, login_time=login_time)
        self.session.add_all((active_user, history_user))

        self.session.commit()

    def user_logout(self, username):
        active_user = self.session.scalar(select(self.ActiveUsers)
                                          .join(self.ActiveUsers.user)
                                          .where(self.AllUsers.username == username))
        self.session.delete(active_user)
        self.session.commit()

    def get_all_users(self):
        return self.session.scalars(select(self.AllUsers))

    def check_user(self, username):
        return self.session.scalar(select(self.AllUsers).where(self.AllUsers.username == username))
    
    def get_public_key(self, username):
        return self.session.scalar(select(self.AllUsers).where(self.AllUsers.username == username)).public_key
    
    def check_contact_is_online(self, username):
        active_user = self.session.scalar(select(self.ActiveUsers)
                                          .join(self.ActiveUsers.user)
                                          .where(self.AllUsers.username == username))
        return bool(active_user)

    def get_pass_hash(self, username):
        return self.session.scalar(select(self.AllUsers).where(self.AllUsers.username == username)).password_hash

    def show_active_users(self):
        return self.session.scalars(select(self.ActiveUsers).join(self.ActiveUsers.user))

    def login_history(self, username=None):
        query = select(self.LoginHistory).join(self.LoginHistory.user)
        if username:
            return self.session.scalars(query.where(self.AllUsers.username == username))
        else:
            return self.session.scalars(query)
    
    def users_events_history(self, username=None):
        query = select(self.UsersEventsHistory).join(self.UsersEventsHistory.user)
        if username:
            return self.session.scalars(query.where(self.AllUsers.username == username))
        else:
            return self.session.scalars(query)

    
    def process_message(self, sender: str, recipient: str):

        self.session.scalar(select(self.UsersEventsHistory)
                            .join(self.UsersEventsHistory.user)
                            .where(self.AllUsers.username == sender)).sent += 1

        self.session.scalar(select(self.UsersEventsHistory)
                            .join(self.UsersEventsHistory.user)
                            .where(self.AllUsers.username == recipient)).received += 1

        self.session.commit()

    def add_contact(self, username: str, contact_username: str):
        user = self.session.scalar(select(self.AllUsers).where(self.AllUsers.username == username))
        contact = self.session.scalar(select(self.AllUsers).where(self.AllUsers.username == contact_username))

        user_in_contacts = self.session.scalar(select(self.UsersContacts)
                                               .join(self.UsersContacts.user)
                                               .where(self.AllUsers.username == username,
                                                      self.UsersContacts.contact_id == contact.id))
        if not contact or user_in_contacts:
            return
      
        self.session.add(self.UsersContacts(user_id=user.id, contact_id=contact.id))
        self.session.commit()
    
    def remove_contact(self, username: str, contact_username: str):
        user = self.session.scalar(select(self.AllUsers).where(self.AllUsers.username == username))
        contact = self.session.scalar(select(self.AllUsers).where(self.AllUsers.username == contact_username))

        user_in_contacts = self.session.scalar(select(self.UsersContacts)
                                               .join(self.UsersContacts.user)
                                               .where(self.AllUsers.username == username,
                                                      self.UsersContacts.contact_id == contact.id))
        if not contact or not user_in_contacts:
            return
      
        self.session.delete(user_in_contacts)
        self.session.commit()

    def get_contacts(self, username: str):
        # я позже разберусь с зависимостями и сделаю здесь всё нормально, но пока так
        contacts = self.session.scalars(select(self.UsersContacts)
                                    .join(self.UsersContacts.user)
                                    .where(self.AllUsers.username == username))
        contacts_list = [self.session.scalar(select(self.AllUsers)
                                             .where(self.AllUsers.id == contact.contact_id)).username\
                         for contact in contacts]
        return contacts_list



if __name__ == '__main__':
    path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'test_server.db')
    print(path)
    server_base = ServerStorage(path)
    server_base.user_login('alesha', '127.0.0.1', 7000)
    server_base.user_login('masha', '127.0.0.2', 5000)
    print('all clients')
    for client in server_base.get_all_users():
        print(f'User {client.username}, last_login {client.last_login.strftime("%d.%m.%Y %H:%M")}')
    print()

    print('active clients')
    for client in server_base.show_active_users():
        print(f'User {client.user.username} connected at {client.login_time.strftime("%d.%m.%Y %H:%M")} '
              f'from {client.ip_address}:{client.port}')
    print()

    print('active clients after removing alesha')
    server_base.user_logout('alesha')
    for client in server_base.show_active_users():
        print(f'User {client.user.username} connected at {client.login_time.strftime("%d.%m.%Y %H:%M")} '
              f'from {client.ip_address}:{client.port}')
    server_base.user_login('alesha', '127.0.0.3', 3000)
    print()

    print('alesha is back')
    print('login history for alesha')
    for client in server_base.login_history('alesha'):
        print(f'User {client.user.username} connected at {client.login_time.strftime("%d.%m.%Y %H:%M")} '
              f'from {client.ip_address}:{client.port}')
    print()

    print('alesha send message to masha')
    server_base.process_message('alesha', 'masha')
    for client in server_base.users_events_history():
        print(f'User {client.user.username} sent {client.sent} messages, received {client.received}')
    print()


    print('add_contact masha to alesha')
    server_base.add_contact('alesha', 'masha')
    print('add_contact alesha to masha')
    server_base.add_contact('masha', 'alesha')
    print()

    print('Masha contacts:')
    print(', '.join(server_base.get_contacts('masha')))
    print('Alesha contacts:')
    print(', '.join(server_base.get_contacts('alesha')))
        

    print('remove contact alesha from masha')
    server_base.remove_contact('masha', 'alesha')

    print('Masha contacts:')
    print(', '.join(server_base.get_contacts('masha')))