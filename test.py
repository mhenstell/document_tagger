import urwid

def main():
    my_widget = MyWidget()
    palette = [('unselected', 'default', 'default'),
               ('selected', 'standout', 'default', 'bold')]

    urwid.MainLoop(my_widget, palette=palette).run()


class MyWidget(urwid.WidgetWrap):

    def __init__(self):

        n = 10       
        labels = ['selection {}'.format(j) for j in range(n)]

        self.header = urwid.Pile([urwid.AttrMap(urwid.SelectableIcon(label), 'unselected', focus_map='selected') for label in labels])

        self.edit_widgets = [urwid.Edit('', label + ' edit_text') for label in labels]

        self.body = urwid.Filler(self.edit_widgets[0])

        super().__init__(urwid.Frame(header=self.header, body=self.body, focus_part='body'))

        self.update_focus(new_focus_position=0)

    def update_focus(self, new_focus_position=None):
        self.header.focus_item.set_attr_map({None: 'unselected'})

        try:
            self.header.focus_position = new_focus_position
            self.body = urwid.Filler(self.edit_widgets[new_focus_position])

        except IndexError:
            pass

        self.header.focus_item.set_attr_map({None: 'selected'})

        self._w = urwid.Frame(header=self.header, body=self.body, focus_part='body')

    def keypress(self, size, key):

        if key == 'up':
            self.update_focus(new_focus_position=self.header.focus_position - 1)

        if key == 'down':
            self.update_focus(new_focus_position=self.header.focus_position + 1)

        if key in {'Q', 'q'}:
            raise urwid.ExitMainLoop()

        super().keypress(size, key)

main()