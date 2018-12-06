import os
import subprocess
import logging
import urwid

from base_model import Document, Tag

# palette = [
#     (None,  'light gray', 'black'),
#     ('heading', 'black', 'light gray'),
#     ('line', 'black', 'light gray'),
#     ('options', 'dark gray', 'black'),
#     ('focus heading', 'white', 'dark red'),
#     ('focus line', 'black', 'dark red'),
#     ('focus options', 'black', 'light gray'),
#     ('selected', 'white', 'dark blue')]
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
        ('pg smooth',     'dark magenta','black'),
        ('normal', 'white', 'white'),
        ('editfc','white', 'dark blue', 'bold'),
        ('editbx','light gray', 'dark blue'),
        ('editcp','black','light gray', 'standout'),
        ('popbg', 'white', 'dark blue')
        ]
focus_map = {
    'heading': 'focus heading',
    'options': 'focus options',
    'line': 'focus line'}

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

def getDocumentsMatchingTags(tags=[]):
    documents = Document.select()
    for tag in tags:
        documents = [d for d in documents if tag in [t.name for t in d.tags]]
    return documents

def getNewScans():
    files = [f for f in os.listdir(SCANS_DIR) if os.path.isfile(os.path.join(SCANS_DIR, f))]
    files = list(filter(lambda f: '.pdf' in f, files))
    files = [f for f in files if Document.get_or_none(Document.filename == f) == None]
    return files

def importNewDocuments():
    files = getNewScans()
    # log.debug(files)
    for f in files:
        Document.create(filename = f)

class SearchBox(urwid.Edit):
    def __init__(self, text, callback):
        self.callback = callback
        super(SearchBox, self).__init__(text)

    def keypress(self, size, key):
        # log.debug("Edit keypress: %s", key)
        if key == 'enter':
            self.callback(self.get_edit_text())

        return super().keypress(size, key)

class DocumentBrowseWindow(urwid.WidgetWrap):
    def __init__(self):
        self.filter_tags = []
        self.current_selected = 0

        self.listbox = urwid.ListBox(urwid.SimpleFocusListWalker([]))
        self._refresh()

        self.menu = urwid.BoxAdapter(self.listbox, height=len(self.listbox.body))
        self.menu = urwid.AttrMap(self.menu, 'options', focus_map)        
        
        line = urwid.Divider(u'\N{LOWER ONE QUARTER BLOCK}')
        header = urwid.Pile([
            urwid.AttrMap(urwid.Text([u"\n  ", 'Main Menu']), 'heading'),
            urwid.AttrMap(line, 'line'),
            urwid.Divider()])

        search = urwid.BoxAdapter(self.search_box(), height=9)
        widget_list = [header, search, self.menu]

        self.alert = None
        new_files = getNewScans()
        if len(new_files):
            alert = urwid.BoxAdapter(self.alert_box(new_files), height=3)
            widget_list.insert(2, alert)

        self.menu = self._menu(widget_list)
        
        super(DocumentBrowseWindow, self).__init__(MenuButton(['test'], None))

    def _refresh(self):
        """ Refresh the document list so that we see updated tag changes """
        doc_launchers = [DocumentButtonLauncher(d) for d in getDocumentsMatchingTags(self.filter_tags)]
        self.listbox.body = doc_launchers

        if len(self.listbox.body) == 0:
            return

        if self.current_selected >= len(self.listbox.body):
            self.current_selected = len(self.listbox.body) - 1
        self.listbox.set_focus(self.current_selected)

        for dl in doc_launchers:
            urwid.connect_signal(dl, 'click', self._handle_popup_open)
            urwid.connect_signal(dl, 'close', self._handle_popup_close)

    def _handle_popup_open(self):
        """ Store the current list position """
        log.debug("Handling popup open")
        self.current_selected = self.listbox.get_focus()[1]

    def _handle_popup_close(self):
        """ Refresh the listbox incase we changed the tags """
        self._refresh()

    def _menu(self, widget_list):
        return urwid.Filler(urwid.Pile(widget_list), valign='top')

    def handle_tag_search(self, tag_text):
        """ Do tag filtering based on search box """
        log.debug("Handling tag search: %s", tag_text)
        tags = tag_text.split()
        self.filter_tags = tags
        self.current_selected = 0
        self._refresh()

    def handle_text_search(self, text):
        """ Do text filtering based on search box """
        log.debug("Handling text search: %s", text)

        self.current_selected = 0
        self._refresh()

    def import_new_documents(self, button):
        importNewDocuments()
        self._refresh()
        self.menu._original_widget._contents.pop(2)

    def search_box(self):
        """ Compile the tag/text search box """
        tags = SearchBox("Search Tags: ", self.handle_tag_search)
        tag_search = urwid.LineBox(urwid.AttrWrap(tags, 'editbx', 'editfc'))
        
        text = SearchBox("Search Documents: ", self.handle_text_search)
        text_search = urwid.LineBox(urwid.AttrWrap(text, 'editbx', 'editfc'))

        l = [ tag_search,
              urwid.Divider(),
              text_search]
        w = urwid.LineBox(urwid.ListBox(urwid.SimpleListWalker(l)))
        return w

    def alert_box(self, new_files):
        a = MenuButton("Import %s new documents" % len(new_files), self.import_new_documents)
        w = urwid.LineBox(urwid.ListBox(urwid.SimpleListWalker([a])))
        return w

class MenuButton(urwid.Button):
    def __init__(self, caption, callback):
        super(MenuButton, self).__init__(caption)
        if callback != None:
            urwid.connect_signal(self, 'click', callback)

        icon = urwid.AttrMap(urwid.SelectableIcon(
            [u'  \N{BULLET} ', caption], 2), None, 'selected')
        self._w = icon

class NewTag(urwid.Edit):
    """ Wrapper around urwid.Edit, captures 'enter' key"""
    signals = ["enter"]
    def __init__(self, caption):
        super(NewTag, self).__init__(caption)

    def keypress(self, size, key):
        if key == 'enter':
            urwid.emit_signal(self, 'enter', self.get_edit_text())
        return super().keypress(size, key)

class PopUpDialog(urwid.WidgetWrap):
    signals = ['close']
    def __init__(self, doc):
        self.doc = doc
        self.close_button = urwid.Button("done")
        urwid.connect_signal(self.close_button, 'click',
            lambda button:self._emit("close"))

        # Handle NewTag edit box
        self.new_tag = NewTag('New: ')
        urwid.connect_signal(self.new_tag, 'enter', self._handle_new_tag)

        # Tags listbox
        self.listbox = urwid.ListBox(urwid.SimpleFocusListWalker(
                [MenuButton(t.name, None) for t in doc.tags] + [self.new_tag]
            ))

        self.pile = urwid.Pile([urwid.Text(
            "Tags for %s" % doc.filename), urwid.BoxAdapter(self.listbox, 4), self.close_button])
        fill = urwid.Filler(self.pile)
        super().__init__(urwid.AttrWrap(fill, 'popbg'))

    def _handle_new_tag(self, tag_name):
        """ Called when enter pressed on NewTag edit box"""
        log.debug("Handling new tag: %s", tag_name)
        tag, created = Tag.get_or_create(name=tag_name)
        if tag not in self.doc.tags:
            self.listbox.body.insert(-1, MenuButton(tag_name, None))
            tag.documents.add(self.doc)
        self.new_tag.set_edit_text("")

    def keypress(self, size, key):
        # Handle tag deletion
        if key == 'backspace':
            tag_widget = self.pile.focus_item._original_widget.get_focus()[0]
            
            # Don't try to delete NewTag
            if tag_widget != self.new_tag:
                list_body = self.pile.focus_item._original_widget.body
                self.pile.focus_item._original_widget.body = \
                    [i for i in self.pile.focus_item._original_widget.body if i != tag_widget]

                tag_name = tag_widget.get_label()
                log.debug("Deleting tag %s" % tag_name)
                self.doc.tags.remove(Tag.select().where(Tag.name == tag_name))
        elif key == 'esc':
            self._emit("close")
        return super().keypress(size, key)

class DocumentButton(urwid.Button):
    """ Container for the document item in the browse listbox """
    def __init__(self, doc):
        self.doc = doc
        self.separator = u' '
        super(DocumentButton, self).__init__(doc.filename)

        text = [doc.filename]
        text.append(self.separator)
        text.append(self.separator)
        text.append(self.separator)
        for tag in self.doc.tags:
            text.append("@%s " % tag.name)

        if len(self.doc.tags) == 0:
            text.append("<untagged>")

        icon = urwid.AttrMap(urwid.SelectableIcon(
            [u'  \N{BULLET} ', text], 2), None, 'selected')
        self._w = icon

    def keypress(self, size, key):
        if key == ' ':
            self.quicklook()
        else:
            return super(DocumentButton, self).keypress(size, key)

    def quicklook(self):
        working_path = os.path.join(SCANS_DIR, self.doc.filename)
        FNULL = open(os.devnull, 'w')
        subprocess.Popen(['qlmanage', '-p', working_path], stdout=FNULL, stderr=FNULL)

class DocumentButtonLauncher(urwid.PopUpLauncher):
    signals = ['close', 'click']
    def __init__(self, doc):
        self.doc = doc
        super(DocumentButtonLauncher, self).__init__(DocumentButton(doc))
        urwid.connect_signal(self.original_widget, 'click', lambda button: self.open_pop_up())

    def _close(self, arg):
        self.close_pop_up()
        urwid.emit_signal(self, 'close')

    def create_pop_up(self):
        urwid.emit_signal(self, 'click')
        pop_up = PopUpDialog(self.doc)
        urwid.connect_signal(pop_up, 'close', self._close)
        
        return pop_up

    def get_pop_up_parameters(self):
        return {'left': 0, 'top': 1, 'overlay_width': 32, 'overlay_height': 7}

class CascadingBoxes(urwid.WidgetPlaceholder):
    max_box_levels = 4

    def __init__(self, box):
        super(CascadingBoxes, self).__init__(urwid.SolidFill())
        self.box_level = 0
        self.open_box(box)

    def open_box(self, box):
        # self.original_widget = urwid.Overlay(urwid.LineBox(box),
        #     self.original_widget,
        #     align='center', width=('relative', 80),
        #     valign='middle', height=('relative', 80),
        #     min_width=24, min_height=8,
        #     left=self.box_level * 3,
        #     right=(self.max_box_levels - self.box_level - 1) * 3,
        #     top=self.box_level * 2,
        #     bottom=(self.max_box_levels - self.box_level - 1) * 2)
        self.original_widget = self.main_shadow(urwid.AttrWrap(box, 'body'))
        self.box_level += 1

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

    def keypress(self, size, key):
        if key == 'esc' and self.box_level > 1:
            self.original_widget = self.original_widget[0]
            self.box_level -= 1
        else:
            return super(CascadingBoxes, self).keypress(size, key)

# top = CascadingBoxes(menu_top.menu)
top = CascadingBoxes(DocumentBrowseWindow().menu)
urwid.MainLoop(top, palette, pop_ups=True).run()