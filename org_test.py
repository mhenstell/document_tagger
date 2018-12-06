# -*- coding: utf-8 -*-
"""
hierarchical prompt usage example
"""
import os
import subprocess
import signal
import sys
from enum import Enum
from peewee import Model, CharField, TextField, TimestampField, ManyToManyField, SqliteDatabase

from PyInquirer import Token, prompt

DB_FILE = 'documents.db'
SCANS_DIR = "/Users/mhenstell/Desktop/scans"

# CREATE_DOCUMENTS_TABLE = '''CREATE TABLE documents
#                             (filename text,
#                             tag_ids text,
#                             time_added integer,
#                             time_updated integer)'''

# CREATE_ADD_TRIGGER     = '''CREATE TRIGGER add_trigger 
#                             AFTER INSERT ON documents 
#                             FOR EACH ROW 
#                             BEGIN 
#                                 UPDATE documents 
#                                 SET time_added = strftime('%s', 'now')
#                                 WHERE rowid = last_insert_rowid(); 
#                             END'''

# CREATE_UPDATE_TRIGGER  = '''CREATE TRIGGER update_trigger 
#                             AFTER UPDATE ON documents
#                             FOR EACH ROW
#                             BEGIN
#                                 UPDATE documents SET time_updated = strftime('%s', 'now')
#                                 WHERE rowid = old.rowid;
#                             END'''

def soft_exit():
    print("Quitting...")
    sys.exit(0)

class Mode(Enum):
    ADD = 0
    BROWSE = 1

class NoSelectionError(Exception):
    pass
class GoBack(Exception):
    pass

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
        




# tagged_files = {}

def quicklook(doc):
    working_path = os.path.join(SCANS_DIR, doc.filename)
    FNULL = open(os.devnull, 'w')
    subprocess.Popen(['qlmanage', '-p', working_path], stdout=FNULL, stderr=FNULL)

def new_file_tagging(new_entries):

    print("New untagged documents:")
    file_prompt = {
        'type': 'list',
        'name': 'file',
        'message': 'Select a document',
        'choices': new_entries.keys()
    }
    answers = prompt(file_prompt)
    doc = new_entries[answers['file']]
    quicklook(doc)
    
    tag_prompt = {
        'type': 'input',
        'name': 'tags',
        'message': 'Tags for file:'
    }
    answers = prompt(tag_prompt)
    tags = answers['tags'].split()

    for tag_name in tags:
        tag, created = Tag.get_or_create(name=tag_name)
        doc.tags.add(tag)


def main_menu():
    menu_prompt = {
        'type': 'list',
        'name': 'selection',
        'message': 'Main Menu:',
        'choices': ['Tag New Files', 'Browse Tags']
    }
    
    p = prompt(menu_prompt)
    if 'selection' in p:
        choice = p['selection'][1]

        if choice == 'Tag New Files':
            return Mode.ADD
        elif choice == 'Browse Tags':
            return Mode.BROWSE
    else:
        raise NoSelectionError

def first_run():
    create_prompt = {
        'type': 'confirm',
        'message': 'Database file not found. Create %s?' % DB_FILE,
        'name': 'create',
        'default': False
    }
    answer = prompt(create_prompt)
    if 'create' not in answer or answer['create'] is False:
        soft_exit()

    db.connect()

    DocumentTags = Tag.documents.get_through_model()
    db.create_tables([Document, Tag, DocumentTags])
    print("Database created")

def import_new_files():
    dir_list = os.listdir(SCANS_DIR)
    # path_maker = lambda file_name: os.path.join(SCANS_DIR, file_name)
    files = [f for f in dir_list if os.path.isfile(os.path.join(SCANS_DIR, f))]
    files = list(filter(lambda f: '.DS_Store' not in f, files))

    new_entries = {}
    for f in files:
        doc, created = Document.get_or_create(filename=f)

        if doc.tags.select().count() == 0:
            new_entries[doc.filename] = doc

    return new_entries

def prompt_for_tag():
    tags = Tag.select()
    
    tag_prompt = {
        'type': 'list',
        'message': 'Select tag:',
        'name': 'tag',
        'choices': [t.name for t in tags]
    }

    answer = prompt(tag_prompt)

    if 'tag' not in answer:
        raise NoSelectionError

    tag = Tag.get(Tag.name == answer['tag'][1])
    return tag

def prompt_for_document_by_tag(tag):
    document_list = []
    for document in tag.documents:
        doc_tags = [t.name for t in document.tags]
        doc_display = "%s [%s]" % (document.filename, ' '.join(doc_tags))
        # document_list[doc_display] = document
        document_list.append({'name': doc_display, 'value': document})

    document_list.append('Back')

    document_prompt = {
        'type': 'list',
        'message': 'Select a Document:',
        'name': 'document',
        'choices': document_list
    }
    answer = prompt(document_prompt)

    if 'document' not in answer:
        raise NoSelectionError

    if answer['document'][1] == 'Back':
        raise GoBack

    return answer['document'][1]

def browse_tags():
    while True:
        try:
            tag = prompt_for_tag()
    
            while True:
                try:
                    document = prompt_for_document_by_tag(tag)
                
                    quicklook(document)

                    edit_prompt = {
                        'type': 'list',
                        'message': '',
                        'name': 'action',
                        'choices': ['Back to %s' % tag.name, 'Edit Tags', 'Main Menu']
                    }

                    answer = prompt(edit_prompt)
                    if answer['action'][1] == 'Back to %s' % tag.name:
                        continue
                    elif answer['action'][1] == 'Edit Tags':
                        edit_tags(document)
                    elif answer['action'][1] == 'Main Menu':
                        break

                except GoBack:
                    break
        except GoBack:
            break

def edit_tags(doc):
    tags = [t.name for t in doc.tags]

    input_prompt = {
        'type': 'input',
        'message': 'Edit tags:',
        'default': ' '.join(tags),
        'name': 'tags'
    }
    answer = prompt(input_prompt)
    if 'tags' not in answer:
        raise NoSelectionError

    doc.tags.clear()

    for tag_name in answer['tags'].split():
        tag, created = Tag.get_or_create(name=tag_name)
        tag.documents.add(doc)

def main():
    # signal.signal(signal.SIGINT, signal_handler)
    # main_menu()

    if not os.path.exists(DB_FILE):
        first_run()
    db.connect(reuse_if_open=True)

    try:
        mode = main_menu()

        health_tag, created = Tag.get_or_create(name="health")
        health_tag.save()

        if mode == Mode.ADD:
            new_entries = import_new_files()
            if len(new_entries) == 0:
                print("No new entries")
            else:
                new_file_tagging(new_entries)
        
        elif mode == Mode.BROWSE:
            while True:
                try:
                    browse_tags()
                except GoBack:
                    break


    except NoSelectionError:
        soft_exit()

    # exit_house()


if __name__ == '__main__':
    while True:
        main()
