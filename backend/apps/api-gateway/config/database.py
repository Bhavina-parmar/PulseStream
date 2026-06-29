from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config.settings import settings

engine=create_engine(settings.database_url) #create SQLAlchemy engine
SessionLocal= sessionmaker(autocommit=False, autoflush=False, bind=engine) #craete sessionlocal for opening/closing database sessions
Base=declarative_base() #create base class
def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()