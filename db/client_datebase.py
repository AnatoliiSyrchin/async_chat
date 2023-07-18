
from sqlalchemy.orm import Session, Mapped, DeclarativeBase, mapped_column, relationship
from sqlalchemy import create_engine, String, select, ForeignKey
from datetime import datetime


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
        from_user: Mapped[str] = mapped_column(String(30))
        to_user: Mapped[str] = mapped_column(String(30))
        message: Mapped[str]
        date: Mapped[datetime] = mapped_column(default=datetime.now())


    def __init__(self, prefix=''):
        self.engine = create_engine(f'sqlite:///db/{prefix}client.db', echo=False, pool_recycle=3600)
        self.Base.metadata.create_all(self.engine)

        with Session(self.engine) as self.session:
            self.session.query(self.AllUsers).delete()
            self.session.commit()

    def fill_all_users(self, users):
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
    
    def save_message(self, from_user, to_user, message):
        self.session.add(self.MessageHistory(from_user=from_user, to_user=to_user, message=message))
        self.session.commit()
    
    def get_message_history(self, from_user=None, to_user=None):
        query = select(self.MessageHistory)
        if from_user:
            return self.session.scalars(query.where(self.MessageHistory.from_user == from_user))
        elif to_user:
            return self.session.scalars(query.where(self.MessageHistory.to_user == to_user))
        else:
            return self.session.scalars(query)

   
if __name__ == '__main__':
    client_datebase = ClientStorage(prefix='test_')

    print(f'Users added to datebase oleg, anna, dmitriy')
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

    print('anna send message to dmitriy')
    client_datebase.save_message('anna', 'dmitriy', 'privet')
    print('oleg send message to anna')
    client_datebase.save_message('oleg', 'anna', 'privet')
    print('anna send message to oleg')
    client_datebase.save_message('anna', 'oleg', 'privet')
    print()

    print('all message history')
    for message in client_datebase.get_message_history():
        print(f'From user {message.from_user}, to user: {message.to_user}, message: {message.message}')
    
    print('message history from anna')
    for message in client_datebase.get_message_history(from_user='anna'):
        print(f'From user {message.from_user}, to user: {message.to_user}, message: {message.message}')
    print()
    
    print('removed contact oleg')
    client_datebase.del_contact('oleg')

    print('contacts in base:')
    print(f'{", ".join(client_datebase.get_contacts())}')
