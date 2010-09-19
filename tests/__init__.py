#
engine = 'sqlite:///:memory:'
engine = 'sqlite:///localization.db'

def do_it(test):
    """ a marker for nose selection
    """
    test.do_it = True
    return test
