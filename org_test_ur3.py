import os
import subprocess
import logging
import urwid
from peewee import Model, CharField, TextField, TimestampField, ManyToManyField, SqliteDatabase



logging.basicConfig(filename='urwid_test.log',
                            filemode='a',
                            format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                            datefmt='%H:%M:%S',
                            level=logging.DEBUG)

logging.info("Starting urwid test...")
log = logging.getLogger('urwid_test')

logging.getLogger('peewee').setLevel(logging.INFO)


SCANS_DIR = "/Users/mhenstell/Desktop/scans"
DB_FILE = 'documents.db'
db = SqliteDatabase('documents.db')

class BaseModel(Model):
    class Meta:
        database = db

class Document(BaseModel):
    filename = CharField(unique=True)
    # tag_ids = CharField(null=True)
    ts_added = TimestampField()
    ts_updated = TimestampField()

    def __repr__(self):
        return self.filename

class Tag(BaseModel):
    name = CharField(unique=True)
    documents = ManyToManyField(Document, backref='tags')



class MainMenu(urwid.WidgetWrap):
    palette = [
        ('body',         'black',      'light gray', 'standout'),
        ('header',       'white',      'dark red',   'bold'),
        ('screen edge',  'light blue', 'dark cyan'),
        ('main shadow',  'dark gray',  'black'),
        ('line',         'black',      'light gray', 'standout'),
        ('bg background','light gray', 'black'),
        ('bg 1',         'black',      'dark blue', 'standout'),
        ('bg 1 smooth',  'dark blue',  'black'),
        ('bg 2',         'black',      'dark cyan', 'standout'),
        ('bg 2 smooth',  'dark cyan',  'black'),
        ('button normal','light gray', 'dark blue', 'standout'),
        ('button select','white',      'dark green'),
        ('line',         'black',      'light gray', 'standout'),
        ('pg normal',    'white',      'black', 'standout'),
        ('pg complete',  'white',      'dark magenta'),
        ('pg smooth',     'dark magenta','black')
        ]

    focus_map = {
        'heading': 'focus heading',
        'options': 'focus options',
        'line': 'focus line'}

    def __init__(self):
        

        caption = "Main Menu"
        # def _handle_close():
        #     log.debug("Updating choices: %s", choices)
        #     self._refresh(caption, choices=None)

        # for c in choices:
        #     if type(c) == DocumentButtonLauncher:
        #         urwid.connect_signal(c, 'close', _handle_close)

        
        
        super(MainMenu, self).__init__(self.main_window())

    def assembleListWalker(self, caption, choices):
        
        return urwid.SimpleFocusListWalker([
                            
                            urwid.Divider(),
                        ] + choices + [urwid.Divider()])

    def _refresh(self, caption, choices=None):
        self.listbox.body = self.assembleListWalker(caption, [])

    def main_shadow(self, w):
        """Wrap a shadow and background around widget w."""
        bg = urwid.AttrWrap(urwid.SolidFill(u"\u2592"), 'screen edge')
        shadow = urwid.AttrWrap(urwid.SolidFill(u" "), 'main shadow')

        bg = urwid.Overlay( shadow, bg,
            ('fixed left', 3), ('fixed right', 1),
            ('fixed top', 2), ('fixed bottom', 1))
        w = urwid.Overlay( w, bg,
            ('fixed left', 2), ('fixed right', 3),
            ('fixed top', 1), ('fixed bottom', 2))
        return w

    def search_box(self):

        l = [ urwid.Text("Tags"),
              urwid.Divider(),
              urwid.Text("Search")]
        w = urwid.LineBox(urwid.ListBox(urwid.SimpleListWalker(l)))
        return w

    def main_window(self):
        self.listbox = urwid.ListBox([])
        self._refresh('Main Menu')

        line = urwid.Divider(u'\N{LOWER ONE QUARTER BLOCK}')
        header = urwid.ListBox([urwid.AttrMap(urwid.Text([u"\n  ", 'Main Menu']), 'heading'), urwid.AttrMap(line, 'line')])
        
        s = self.search_box()
        # lb = self.listbox
        div = urwid.Divider()
        
        w = urwid.Filler(urwid.Pile('pack',[header, s]), 'top')
        w = urwid.AttrWrap(w, 'body')
        w = self.main_shadow(w)
        return w


    def open_menu(self, button):
        top.open_box(self.menu)



menu_top = \
    MainMenu()




# class CascadingBoxes(urwid.WidgetPlaceholder):
#     max_box_levels = 4

#     def __init__(self, box):
#         super(CascadingBoxes, self).__init__(urwid.SolidFill())
#         self.box_level = 0
#         self.open_box(box)

#     def open_box(self, box):
#         self.view = urwid.Overlay(urwid.LineBox(box),
#             self.original_widget,
#             align='center', width=('relative', 80),
#             valign='middle', height=('relative', 80),
#             min_width=24, min_height=8,
#             left=self.box_level * 3,
#             right=(self.max_box_levels - self.box_level - 1) * 3,
#             top=self.box_level * 2,
#             bottom=(self.max_box_levels - self.box_level - 1) * 2)
#         self.box_level += 1

#     # def keypress(self, size, key):
#     #     if key == 'esc' and self.box_level > 1:
#     #         self.original_widget = self.original_widget[0]
#     #         self.box_level -= 1
#     #     else:
#     #         return super(CascadingBoxes, self).keypress(size, key)


class MaxController:

    def __init__(self):
        self.menu = MainMenu()
        self.view = urwid.AttrMap(self.menu, 'options', self.menu.focus_map)

    def main(self):
        self.loop = urwid.MainLoop(self.view, self.menu.palette)
        self.loop.run()


def main():
    MaxController().main()

# top = CascadingBoxes(menu_top.menu)
# urwid.MainLoop(top, palette, pop_ups=True).run()



if __name__ == '__main__':
    main()