import altair
import ipywidgets as widgets
from IPython.display import display, clear_output
import pandas as pd


def interact_with(df, ndims=3, **kwargs):
    """
    Interactively view a DataFrame.

    Parameters
    ----------
    df : DataFrame
        The DataFrame to interact with
    ndims : int, optional
        The number of dimensions wished to encode (the number of rows with
        encoding/data/function/data_type).

    Notes
    -----
    In the Jupyter notebook, display a widget
    to allow you to selectively plot columns to plot/encode/etc.

    """
    return Interact(df, ndims=ndims, **kwargs)


class Interact:
    """
    The class to that provides the interaction interface.

    Public member functions
    -----------------------
    - Interact.__init__(self, df, ndims=3, show=True)
    - Interact.update(self, button):
    - Interact.plot(self, settings, show=True):

    """
    def __init__(self, df, ndims=3, show=True):
        if not isinstance(df, pd.core.frame.DataFrame):
            raise ValueError('Interact takes a DataFrame as input')
        columns = [None] + _get_columns(df)
        encodings = _get_encodings()
        self.df = df
        encodings = [{'encoding': encoding}
                     for encoding in encodings[:ndims]]
        self.settings = {'mark': {'mark': 'mark_point'},
                         'encodings': encodings}

        self.controller = self._generate_controller(columns, ndims)
        self.show = show
        if self.show:
            display(self.controller)

        self.plot(self.settings, show=show)

    def _show_advanced(self, button, disable=1):
        if 'mark' in button.title:
            disable = 0

        row = button.row
        encoding = self.controller.children[row].children[disable].value
        adv = _get_advanced_settings(encoding)
        controllers = [_controllers_for(a) for a in adv]
        for c in controllers:
            c.row = row
            c.observe(self.update, names='value')

        visible = self.controller.children[row].children[-1].visible
        self.controller.children[row].children[disable].disabled = not visible
        self.controller.children[row].children[-1].visible = not visible
        self.controller.children[row].children[-1].children = controllers

    def _create_shelf(self, columns, i=0):
        """ Creates shelf to plot a dimension (includes buttons
        for data column, encoding, data type, aggregate)"""
        encodings = _get_encodings()

        cols = widgets.Dropdown(options=columns, description='encode')
        encoding = widgets.Dropdown(options=encodings, description='as',
                                    value=encodings[i])
        encoding.layout.width = '20%'

        adv = widgets.HBox(children=[], visible=False)
        adv.layout.display = 'none'

        button = widgets.Button(description='options')
        button.on_click(self._show_advanced)
        button.layout.width = '10%'

        # The callbacks when the button is clicked
        encoding.observe(self.update, names='value')
        cols.observe(self.update, names='value')

        # Making sure we know what row we're in in the callbacks
        encoding.row = cols.row = button.row = adv.row = i

        # Have the titles so we know what button we're editing
        encoding.title = 'encoding'
        cols.title = 'column'
        button.title = 'button'
        adv.title = 'advanced'

        return widgets.HBox([cols, encoding, button, adv])

    def update(self, event):
        """
        Given a button-clicking event, update the encoding settings.

        Parameters
        ----------
        event : dict
            Dictionary describing event. Assumed to have keys ['owner', 'new',
            'old'] with the key corresponding to owner having properties [row,
            title, value]

        Plots the function at the end of the update (this function is called on
        click).
        """
        index = event['owner'].row
        title = event['owner'].title
        value = event['owner'].value
        if index == -1:
            self.settings['mark'][title] = event['new']
        else:
            if title == 'type' and 'auto' in value:
                self.settings['encodings'][index].pop('type', None)
            if title == 'text':
                if value is '':
                    self.settings['encodings'][index].pop('text', None)
                else:
                    self.settings['encodings'][index]['column'] = value
            else:
                if event['new'] is None:
                    self.settings['encodings'][index].pop(title)
                else:
                    self.settings['encodings'][index][title] = event['new']
        self.plot(self.settings)

    def plot(self, settings, show=True):
        """ Assumes nothing in settings is None (i.e., there are no keys in
        settings such that settings[key] == None"""
        kwargs = {e['encoding']: _get_plot_command(e)
                  for e in self.settings['encodings']}

        mark_opts = {k: v for k, v in self.settings['mark'].items()}
        mark = mark_opts.pop('mark')
        Chart_mark = getattr(altair.Chart(self.df), mark)
        self.chart = Chart_mark(**mark_opts).encode(**kwargs)
        if show and self.show:
            clear_output()
            display(self.chart)

    def _generate_controller(self, columns, ndims):
        marks = _get_marks()
        # mark button
        mark_choose = widgets.Dropdown(options=marks, description='Marks')
        mark_choose.observe(self.update, names='value')
        mark_choose.layout.width = '20%'
        mark_choose.row = -1
        mark_choose.title = 'mark'

        # mark options button
        mark_but = widgets.Button(description='options')
        mark_but.layout.width = '10%'
        mark_but.row = -1
        mark_but.title = 'mark_button'

        # Mark options
        mark_opt = widgets.VBox(children=[], visible=False)
        mark_but.on_click(self._show_advanced)
        mark_opt.title = 'mark_options'
        mark_opt.layout.width = '300px'


        dims = [self._create_shelf(columns, i=i) for i in range(ndims)]

        choices = dims + [widgets.HBox([mark_choose, mark_but, mark_opt])]
        return widgets.VBox(choices)


def _get_columns(df):
    return list(df.columns) + ['*']


def _get_types():
    return ['quantitative', 'ordinal', 'nominal', 'temporal']


def _get_encodings():
    return ['x', 'y', 'color', 'text', 'row', 'column',
            'opacity', 'shape', 'size']


def _get_functions():
    return ['mean', 'min', 'max', 'median', 'average', 'sum',
            'count', 'distinct', 'variance', 'stdev', 'q1', 'q3',
            'argmin', 'argmax']


def _get_marks():
    """
    >>> _get_marks()[0]
    'mark_point'
    """
    return ['mark_' + f for f in ['point', 'circle', 'line', 'bar', 'tick',
                                  'text', 'square', 'rule', 'area']]

def _get_mark_params():
    return ['color', 'applyColorToBackground', 'shortTimeLabels']


def _get_advanced_settings(e):
    """
    Given string encoding (e.g. 'x'), returns a dictionary

    >>> _get_advanced_settings('x')
    ['type', 'bin', 'aggregate', 'zero', 'scale']
    """
    adv_settings = {e: ['type', 'bin', 'aggregate']
                    for e in _get_encodings()}
    adv_settings['x'] += ['zero', 'scale']
    adv_settings['y'] += ['zero', 'scale']
    adv_settings['text'] += ['text']

    mark_settings = {mark: _get_mark_params() for mark in _get_marks()}
    adv_settings.update(mark_settings)
    return adv_settings[e]


def _controllers_for(opt):
    """
    Give a string representing the parameter represented, find the appropriate
    command.

    """
    colors = [None, 'blue', 'red', 'green', 'black']
    controllers = {'type': widgets.Dropdown(options=['auto detect'] +\
                           _get_types(), description='type'),
                   'bin': widgets.Checkbox(description='bin'),
                   'aggregate': widgets.Dropdown(options=[None] +\
                                _get_functions(), description='aggregate'),
                   'zero': widgets.Checkbox(description='zero'),
                   'text': widgets.Text(description='text value'),
                   'scale': widgets.Dropdown(options=['linear', 'log'],
                                             description='scale'),
                    'color': widgets.Dropdown(options=colors,
                                             description='main color'),
                    'applyColorToBackground': widgets.Checkbox(description='applyColorToBackground'),
                    'shortTimeLabels': widgets.Checkbox(description='shortTimeLabels')
                  }

    for title, controller in controllers.items():
        controller.title = title
        if 'Checkbox' in str(controller):
            # traits = dir(controller.layout)
            # traits = [t for t in traits if t[0] != '_']
            controller.layout.max_width = '200ex'
            # controller.layout.min_width = '100ex'
            # controller.layout.width = '150ex'

    return controllers[opt]


def _get_plot_command(e):
    """ Given a function, data type and data column name,
    find the plot command

    >>> e = {'encoding': 'x', 'column': 'petalWidth', 'scale': 'log'}
    >>> r = _get_plot_command(e)
    >>> assert r.to_dict() == {'field': 'petalWidth', 'scale': {'type': 'log'}}
    """
    d = {k: v for k, v in e.items()}
    if 'column' not in e:
        return

    encoding = d.pop('encoding')
    column = d.pop('column')

    scale = {}
    if any([key in d for key in ['scale', 'zero']]):
        scale = {'scale': altair.Scale(type=d.pop('scale', None),
                                       zero=d.pop('zero', None))}

    d.update(scale)
    return getattr(altair, encoding.capitalize())(column, **d)
