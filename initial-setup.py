import pickle
from pathlib import Path
import joseconfig as jcfg

# touch files
Path(jcfg.jcoin_path).touch()
Path('db/jose-data.txt').touch()

def initialize_db(path):
    with open(path, 'wb') as f:
        pickle.dump({}, f)

# initialize databases
initialize_db(jcfg.jcoin_path)
initialize_db('ext/josememes.db')
