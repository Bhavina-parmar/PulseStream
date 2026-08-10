from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config.settings import settings

engine = create_engine(
    settings.database_url,
    pool_size=50,
    max_overflow=100,
    pool_timeout=30,
)

SessionLocal= sessionmaker(autocommit=False, autoflush=False, bind=engine) #craete sessionlocal for opening/closing database sessions
Base=declarative_base() #create base class
def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()