from dotenv import dotenv_values
import os

ENV = {
    **os.environ,
    **dotenv_values(".env"),
    **dotenv_values(".env.local")
}
