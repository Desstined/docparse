from src.db.session import engine, SessionLocal
from src.db.models import Base, User
from src.api.auth.utils import get_password_hash
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db():
    """Initialize database and create default admin user."""
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")
    
    # Create default admin user if it doesn't exist
    db = SessionLocal()
    try:
        logger.info("Checking for admin user...")
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            logger.info("Creating default admin user...")
            hashed_password = get_password_hash("admin123")
            admin_user = User(
                username="admin",
                email="admin@example.com",
                hashed_password=hashed_password,
                is_active=True,
                is_superuser=True
            )
            db.add(admin_user)
            db.commit()
            logger.info("Default admin user created successfully")
            logger.info("Admin credentials: username=admin, password=admin123")
        else:
            logger.info("Admin user already exists")
    except Exception as e:
        logger.error(f"Error creating admin user: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    init_db() 