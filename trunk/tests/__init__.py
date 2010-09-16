#
engine = 'sqlite:///localization.db'
engine = 'sqlite:///:memory:'

def do_it(test):
    """ a marker for nose selection
    """
    test.do_it = True
    return test
