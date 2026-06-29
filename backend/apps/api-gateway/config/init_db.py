from config.database import Base,engine
from models.user import User
from models.event import Event


def init_db():
    print("Creating database tables.....")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")

if __name__=="__main__":
    init_db()