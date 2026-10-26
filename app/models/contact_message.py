# =============================================================
# Agri LMS — Contact Message Model
# =============================================================
from datetime import datetime
from app.extensions import db


class ContactMessage(db.Model):
    """Stores messages submitted through the contact form."""

    __tablename__ = 'contact_messages'

    id           = db.Column(db.Integer, primary_key=True)
    sender_name  = db.Column(db.String(150), nullable=False)
    sender_email = db.Column(db.String(150), nullable=False)
    sender_phone = db.Column(db.String(20),  nullable=True)
    subject      = db.Column(db.String(300), nullable=False)
    message      = db.Column(db.Text,        nullable=False)
    is_read      = db.Column(db.Boolean, default=False, nullable=False)
    is_replied   = db.Column(db.Boolean, default=False, nullable=False)
    admin_notes  = db.Column(db.Text, nullable=True)
    date_sent    = db.Column(db.DateTime, default=datetime.utcnow,
                             nullable=False)

    def __repr__(self):
        return (f'<ContactMessage id={self.id} '
                f'from={self.sender_email}>')