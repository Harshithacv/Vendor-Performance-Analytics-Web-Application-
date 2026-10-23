import logging
import sys
from app.database import SessionLocal
from app.models import User
from app.auth import get_password_hash
from app.services.dataset_loader import load_initial_dataset

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("seed_data")

def seed():
    db = SessionLocal()
    try:
        logger.info("Starting seed process...")
        
        # 1. Ensure default admin user exists
        admin = db.query(User).filter(User.email == "admin@vendoranalytics.com").first()
        if not admin:
            admin = User(
                name="System Administrator",
                email="admin@vendoranalytics.com",
                password_hash=get_password_hash("admin123"),
                role="admin"
            )
            db.add(admin)
            db.commit()
            logger.info("Created default admin user: admin@vendoranalytics.com / admin123")
        else:
            logger.info("Default admin user already exists.")

        # Ensure analyst user exists for testing role-based permissions
        analyst = db.query(User).filter(User.email == "shashankparutagoudra4@gmail.com").first()
        if not analyst:
            analyst = User(
                name="Shashank (Analyst)",
                email="shashankparutagoudra4@gmail.com",
                password_hash=get_password_hash("admin123"),
                role="analyst"
            )
            db.add(analyst)
            db.commit()
            logger.info("Created default analyst user: shashankparutagoudra4@gmail.com / admin123")
        else:
            logger.info("Default analyst user already exists.")

        # 2. Ingest real dataset files
        logger.info("Loading initial dataset into MySQL...")
        stats = load_initial_dataset(db, sample_limit=50000)
        logger.info(f"Dataset load results: {stats}")
        logger.info("Seed process completed successfully!")
    except Exception as e:
        logger.error(f"Seed process failed: {e}", exc_info=True)
        db.rollback()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    seed()
