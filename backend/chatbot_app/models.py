from mongoengine import Document, StringField, ListField, EmbeddedDocument, EmbeddedDocumentField, DateTimeField
from django.contrib.auth.hashers import make_password, check_password
from datetime import datetime

class ChatMessage(EmbeddedDocument):
    query = StringField(required=True)
    response = StringField(required=True)
    timestamp = DateTimeField(default=datetime.utcnow)

class MongoUser(Document):
    username = StringField(required=True, unique=True)
    password = StringField(required=True)
    history = ListField(EmbeddedDocumentField(ChatMessage))  # ✅ Added this

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)
