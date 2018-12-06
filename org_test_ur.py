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

class MenuButton(urwid.Button):
    def __init__(self, caption, callback):
        super(MenuButton, self).__init__("")
        urwid.connect_signal(self, 'click', callback)
        self._w = urwid.AttrMap(urwid.SelectableIcon(
            [u'  \N{BULLET} ', caption], 2), None, 'selected')

class SubMenu(urwid.WidgetWrap):
    def __init__(self, caption, choices, width=None):
        super(SubMenu, self).__init__(MenuButton(
            [caption], self.open_menu))
        line = urwid.Divider(u'\N{LOWER ONE QUARTER BLOCK}')
        listbox = urwid.ListBox(urwid.SimpleFocusListWalker([
            urwid.AttrMap(urwid.Text([u"\n  ", caption]), 'heading'),
            urwid.AttrMap(line, 'line'),
            urwid.Divider()] + choices + [urwid.Divider()]))
        self.menu = urwid.AttrMap(listbox, 'options')

    def open_menu(self, button):
        top.open_box(self.menu)

class Choice(urwid.WidgetWrap):
    def __init__(self, caption):
        super(Choice, self).__init__(
            MenuButton(caption, self.item_chosen))
        self.caption = caption

    def item_chosen(self, button):
        response = urwid.Text([self.caption])
        done = MenuButton(u'Ok', exit_program)
        response_box = urwid.Filler(urwid.Pile([response, done]))
        top.open_box(urwid.AttrMap(response_box, 'options'))

class DocumentsForTag(SubMenu):
    def __init__(self, tag):
        choices = [Choice('View'), Choice('Edit')]
        documents = [Document(d) for d in tag.documents]
        super(DocumentsForTag, self).__init__(tag.name, documents, width=30)

class Document(Choice):
    def __init__(self, doc):
        tag_names = [t.name for t in doc.tags]
        caption = "%s [%s]" % (doc.filename, ' '.join(tag_names))

        super(Document, self).__init__(caption)

class BrowseTags(SubMenu):
    def __init__(self):
        tags = Tag.select()
        choices = [DocumentsForTag(t) for t in tags]
        super(BrowseTags, self).__init__(u'Browse By Tag', choices)

def exit_program(key):
    raise urwid.ExitMainLoop()

menu_top = SubMenu(u'Main Menu', [
    SubMenu(u'Tag New Scans', [
        SubMenu(u'Accessories', [
            Choice(u'Text Editor'),
            Choice(u'Terminal'),
        ]),
    ]),
    BrowseTags()
        
])

palette = [
    (None,  'light gray', 'black'),
    ('heading', 'black', 'light gray'),
    ('line', 'black', 'light gray'),
    ('options', 'dark gray', 'black'),
    ('focus heading', 'white', 'dark red'),
    ('focus line', 'black', 'dark red'),
    ('focus options', 'black', 'light gray'),
    ('selected', 'white', 'dark blue')]
focus_map = {
    'heading': 'focus heading',
    'options': 'focus options',
    'line': 'focus line'}

class HorizontalBoxes(urwid.Columns):
    def __init__(self):
        super(HorizontalBoxes, self).__init__([], dividechars=1)

    def open_box(self, box):
        if self.contents:
            del self.contents[self.focus_position + 1:]
        self.contents.append((urwid.AttrMap(box, 'options', focus_map),
            self.options('weight')))
        self.focus_position = len(self.contents) - 1



top = HorizontalBoxes()
top.open_box(menu_top.menu)
urwid.MainLoop(urwid.Filler(top, 'middle', 100), palette).run()