import os

def publish():
    print(f'Publishing {os.environ["NAME"]} to JPRQ')
    os.system(f'{os.environ["COMMAND"]} auth {os.environ["AUTH"]}')
    os.system(f'{os.environ["COMMAND"]} http 8080 -s {os.environ["NAME"]} --reconnect')