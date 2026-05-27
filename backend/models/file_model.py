from datetime import datetime
import pytz
from backend.config.db_config import db

# IST timezone
IST = pytz.timezone('Asia/Kolkata')

def ist_time():
    return datetime.now(IST)

class File(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    filename = db.Column(db.String(200), nullable=False)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable=False
    )
    
    uploaded_at = db.Column(
    db.DateTime,
    default=ist_time
)
    
    
    file_size = db.Column(
    db.Integer
)
    
    is_deleted = db.Column(
    db.Boolean,
    default=False
)
    

    def __repr__(self):
        return f"<File {self.filename}>"