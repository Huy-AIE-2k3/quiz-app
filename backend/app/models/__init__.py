"""Domain Models Package.

Exports all SQLAlchemy persistent models to ensure complete metadata registration.
"""

from app.models.answer import Answer
from app.models.attempt import Attempt
from app.models.audit_log import AuditLog
from app.models.class_model import Class, ClassMember
from app.models.exam import Exam, ExamClass
from app.models.file import File
from app.models.question import Question
from app.models.session import Session
from app.models.user import User

__all__ = [
    "Answer",
    "Attempt",
    "AuditLog",
    "Class",
    "ClassMember",
    "Exam",
    "ExamClass",
    "File",
    "Question",
    "Session",
    "User",
]
