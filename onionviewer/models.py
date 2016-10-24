from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Unicode

Base = declarative_base()

class OnionAddress(Base):
    __tablename__ = "onion_addresses"

    id = Column(Integer, primary_key=True)

    address = Column(String)
    first_seen = Column(DateTime)
    last_seen = Column(DateTime)
    count = Column(Integer)
    website_title = Column(Unicode)

    def __init__(self):
        self.count = 0 

    def __repr__(self):
        return "<OnionAddress(%r, %r.onion, %r)>" % (self.id, self.address, self.count)
