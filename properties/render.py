__author__ = 'mberger'

from extensions_framework import declarative_property_group
from .. import MaxwellRenderAddon

@MaxwellRenderAddon.addon_register_class
class maxwell_engine(declarative_property_group):
    '''
    Storage class for LuxRender Engine settings.
    '''

    ef_attach_to = ['Scene']

    controls = ['log_verbosity']

    visibility = {}

    alert = {}

    properties = [
        {
            'type': 'bool',
            'attr': 'threads_auto',
            'name': 'Auto Threads',
            'description': 'Let LuxRender decide how many threads to use',
            'default': True
        }

    ]


