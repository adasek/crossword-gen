from dotenv import dotenv_values

ENV = {
    **dotenv_values(".env"),
    **dotenv_values(".env.local")
}
