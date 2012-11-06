__author__ = 'mberger'

# contains a lot of code inspired / shamelessly copied from luxblend25

from extensions_framework import log

def MaxwellLog(*args, popup=False):
    '''
    Send string to AF log, marked as belonging to Mitsuba module.
    Accepts variable args
    '''
    if len(args) > 0:
        log(' '.join(['%s'%a for a in args]), module_name='Maxwell', popup=popup)