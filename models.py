from datetime import datetime
from sqlalchemy.sql import func
from db import db

class CleaningJob(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_name = db.Column(db.String(100), nullable=False)
    original_filename = db.Column(db.String(255))
    output_filename = db.Column(db.String(255))
    original_rows = db.Column(db.Integer)
    cleaned_rows = db.Column(db.Integer)
    columns_count = db.Column(db.Integer)
    missing_values_filled = db.Column(db.Integer)
    duplicates_removed = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, server_default=func.now())

    def __repr__(self):
        return f'<CleaningJob {self.job_name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'job_name': self.job_name,
            'original_filename': self.original_filename,
            'output_filename': self.output_filename,
            'original_rows': self.original_rows,
            'cleaned_rows': self.cleaned_rows,
            'columns_count': self.columns_count,
            'missing_values_filled': self.missing_values_filled,
            'duplicates_removed': self.duplicates_removed,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }