from datetime import datetime

from sqlalchemy.orm import Session, Mapped, DeclarativeBase, mapped_column
from sqlalchemy import create_engine, String, select
from sqlalchemy.sql import default_comparator


class ClientStorage:
    class Base(DeclarativeBase):
        pass

    class AllUsers(Base):
        __tablename__ = 'all_users'

        id: Mapped[int] = mapped_column(primary_key=True)
        username: Mapped[str] = mapped_column(String(30), unique=True)

        def __repr__(self):
            return f'User {self.username}'

    class Contacts(Base):
        __tablename__ = 'contacts'

        id: Mapped[int] = mapped_column(primary_key=True)
        username: Mapped[str] = mapped_column(String(30))

        def __repr__(self):
            return f'User contact {self.username}'

    class MessageHistory(Base):
        __tablename__ = 'message_history'

        id: Mapped[int] = mapped_column(primary_key=True)
        contact: Mapped[str] = mapped_column(String(30))
        direction: Mapped[str] = mapped_column(String(3))
        message: Mapped[str]
        date: Mapped[datetime] = mapped_column(default=datetime.now())

    def __init__(self, prefix=''):
        self.engine = create_engine(f'sqlite:///db/{prefix}client.db', echo=False, pool_recycle=3600)
        self.Base.metadata.create_all(self.engine)

        with Session(self.engine) as self.session:
            self.session.query(self.AllUsers).delete()
            self.session.commit()

    def fill_all_users(self, users):
        self.session.query(self.AllUsers).delete()
        all_users = []
        for username in users:
            all_users.append(self.AllUsers(username=username))
        self.session.add_all(all_users)
        self.session.commit()

    def get_all_users(self):
        return [user.username for user in self.session.scalars(select(self.AllUsers))]

    def get_contacts(self):
        return [user.username for user in self.session.scalars(select(self.Contacts))]

    def add_contact(self, contact_username: str):
        contact = self.session.scalar(select(self.Contacts).where(self.Contacts.username == contact_username))

        if contact:
            return

        self.session.add(self.Contacts(username=contact_username))
        self.session.commit()

    def del_contact(self, username):
        self.session.delete(self.session.scalar(select(self.Contacts).where(self.Contacts.username == username)))
        self.session.commit()

    def check_user(self, username):
        return bool(self.session.scalar(select(self.AllUsers).where(self.AllUsers.username == username)))

    def check_contact(self, username):
        return bool(self.session.scalar(select(self.Contacts).where(self.Contacts.username == username)))

    def save_message(self, contact, direction, message):
        self.session.add(self.MessageHistory(contact=contact, direction=direction, message=message))
        self.session.commit()

    def get_message_history(self, contact=None):
        query = select(self.MessageHistory)
        if contact:
            return self.session.scalars(query.where(self.MessageHistory.contact == contact))
        else:
            return self.session.scalars(query)


if __name__ == '__main__':
    client_datebase = ClientStorage(prefix='test_')

    print('Users added to datebase oleg, anna, dmitriy')
    client_datebase.fill_all_users(['oleg', 'anna', 'dmitriy'])
    print('users in base:')
    print(f'{", ".join(client_datebase.get_all_users())}')
    print()

    print('added contacts oleg, dmitriy')
    client_datebase.add_contact('oleg')
    client_datebase.add_contact('dmitriy')
    print('contacts in base:')
    print(f'{", ".join(client_datebase.get_contacts())}')
    print()

    print('test_client received message from anna')
    client_datebase.save_message('anna', 'in', 'privet')
    print('test_client received message from oleg')
    client_datebase.save_message('oleg', 'in', 'privet')
    print('test_client send message to anna')
    client_datebase.save_message('anna', 'out', 'privet')
    print('test_client send message to dmitriy')
    client_datebase.save_message('dmitriy', 'out', 'privet')
    print()

    print('all message history')
    for message in client_datebase.get_message_history():
        print(f'with user {message.contact}, direction: {message.direction}, message: {message.message}')

    print('message history from anna')
    for message in client_datebase.get_message_history(contact='anna'):
        print(f'with user {message.contact}, direction: {message.direction}, message: {message.message}')
    print()

    print('removed contact oleg')
    client_datebase.del_contact('oleg')

    print('contacts in base:')
    print(f'{", ".join(client_datebase.get_contacts())}')
