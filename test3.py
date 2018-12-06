import urwid


# create a palette defining bold attribute
PALETTE = [
    ('bold', 'bold', ''),
]


class BoldValuesList(urwid.WidgetWrap):
    """Show a list of key values, with values in bold
    """
    def __init__(self, values):
        self.separator = u', '
        self.values = values
        self.text = urwid.Text(self._build_text())
        super(BoldValuesList, self).__init__(self.text)

    def _build_text(self):
        # build text markup -- see:
        # http://urwid.org/manual/displayattributes.html#text-markup
        texts = []
        for i, (k, v) in enumerate(self.values):
            texts.append(u'%s: ' % k)
            texts.append(('bold', u'%s' % v))
            if i < len(self.values) - 1:
                texts.append(self.separator)
        return texts


def show_or_exit(key):
    "Exit if user press Q or Esc"
    if key in ('q', 'Q', 'esc'):
        raise urwid.ExitMainLoop()


txt = BoldValuesList([
    (u'Employees', 45),
    (u'Males', 20),
    (u'Females', 25),
])
filler = urwid.Filler(txt, 'top')

# create the main loop wiring the widget, the palette and input handler
loop = urwid.MainLoop(filler, PALETTE, unhandled_input=show_or_exit)
loop.run()