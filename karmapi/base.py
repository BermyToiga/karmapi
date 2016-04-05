""" Karma Pi base 

get(path): get data at path

build(path):  build data at path

get_meta(path):  get meta data for path

"""
import os
import importlib
import json

BASE_FOLDER = '.'

class Parms:
    pass

def find_path(path, paths):
    """ Find first matching path in paths 

    Paths is a dictionary.

    The values are dictionaries too, with a path key.
    """
    for key, target in paths.items():

        parms = match_path(path, target['path'])

        if parms:
            return target, parms

    return False

CASTS = dict(int=int, float=float)


def match_path(path, target_path):
    """ See if path matches target """
    fields = path.split('/')
    target_fields = target_path.split('/')

    parms = Parms()
    for field, target in zip(fields, target_fields):
        if target.startswith('<'):

            # drop the <>'s
            name = target[1:-1]

            if ':' in name:
                typehint, name = name.split(':')

                field = CASTS.get(typehint, str)(field)

            setattr(parms, name, field)

        else:
            if field != target:
                return None

    return parms


def meta_data_match(path, key='gets'):
    """ Work our way along path looking for a match """

    folders = path.split('/')

    bases = []
    relatives = folders[1:]
    
    for folder in folders:
        bases.insert(0, folder)
    
        base = '/'.join(bases)
        relative_path = '/'.join(relatives)
        del relatives[0]
        
        meta = load_meta_path(base)

        match = find_path(relative_path, meta.get(key, {}))

        if match:
            target, parms = match
            parms.__dict__.update(target)
            
            return dict(base=base,
                        path=relative_path,
                        target=target,
                        parms=parms)
    
def build(path):
    """ Dispatch to the appropriate function 

    NB flask has already solved this.
    """
    return dispatch(path, key='builds')

def get(path):
    """ Get data for a path """
    return dispatch(path, key='gets')
    

def dispatch(path, key='gets'):
    """  Dispatch a function call """

    # work our way down path looking for a meta data match
    match = meta_data_match(path, key)

    if not match:
        raise AttributeError("Unrecognised path: {}".format(path))

    # unpack match return value
    base = match['base']
    target = match['target']
    parms = match['parms']
    relative_path = match['path']

    print('BASE:', base)
    print('Relative_path:', relative_path)

    old_dir = os.getcwd()
    try:
        os.chdir(base)

        # extract function to call
        function = get_item(target.get('karma'))

        result = function(relative_path, parms)
        
    finally:
        os.chdir(old_dir)

    # Call the function
    return result


def get_all_meta_data(path):
    """ Spin along a path gathering up all meta data """
    meta = {}

    fields = path.split('/')
    path = []
    for field in fields:
        path.append(field)

        meta_data = meta.update(
            load_meta_path('/'.join(path)))

    return meta
        
def load_meta_path(path):
    """ Load meta data a path if it exists """
    filename = os.path.join(path, 'meta.json')
    if os.path.exists(filename):
        with open(filename) as infile:
            return json.loads(infile.read())

    # return empty dictionary if there is no meta data here
    return {}

def get_item(path):
    """ Given a path, return the item

    Item is usually some sort of python callable.

    It could be a function or a class name.
    """
    path = path.split('.')

    module_name = '.'.join(path[:-1])

    module = importlib.import_module(module_name)

    return getattr(module, path[-1])
    