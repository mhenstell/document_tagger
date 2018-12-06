from peewee import Model, CharField, TextField, TimestampField, ManyToManyField, SqliteDatabase

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