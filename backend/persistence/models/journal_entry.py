import uuid
from sqlalchemy import Column, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from backend.persistence.base import Base, TimestampMixin

class JournalEntryModel(Base, TimestampMixin):
    __tablename__ = "journal_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False, index=True)
    content = Column(Text, nullable=False)

    # Relationships
    case = relationship("Case", back_populates="journal_entries")
