import os

from dotenv import dotenv_values

ENV = {
    **os.environ,
    **dotenv_values(".env"),
    **dotenv_values(".env.local")
}
