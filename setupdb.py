from sqlalchemy import create_engine, text
import json



def run_file(filename='dbsetup.sql'):

    configfile = './MainAPI/src/config.json'

    with open(configfile, 'r') as file:
        configs = json.load(file)

    engine = create_engine(configs['database']['uri'])

    with engine.connect() as conn:
        with open(filename, 'r')  as file:
            queries = file.read().split(';')
            for q in queries:
                try: 
                    conn.execute(text(q))
                    # print('*'*25 + '\n' + f'Executed SQL statement: {q}')
                
                except Exception as e:
                    print(f'Failed SQL statement: {q}.  Error: {e}')


if __name__ == '__main__':
    print('SETTING UP DATABASE')
    run_file()