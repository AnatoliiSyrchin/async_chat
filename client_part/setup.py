from setuptools import setup, find_packages

setup(name="best_chat_client",
      version="0.0.1",
      description="best_chat_client",
      author="Anatoliy Syrchin",
      author_email="9779930@mail.ru",
      packages=find_packages(),
      install_requires=['PyQt5', 'sqlalchemy', 'pycryptodome', 'pycryptodomex']
      )