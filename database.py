import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError
from models import Base

# Setup logging
logger = logging.getLogger(__name__)

# Get database connection string from environment variable
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/werd_tracker")

# Create engine with connection pooling
try:
    engine = create_engine(
        DATABASE_URL,
        poolclass=QueuePool,
        pool_size=10,
        max_overflow=20,
        pool_timeout=30,
        pool_recycle=1800
    )
    logger.info("Database engine created successfully")
except Exception as e:
    logger.critical(f"Failed to create database engine: {e}")
    raise

# Create session factory
SessionFactory = sessionmaker(bind=engine)

# Create scoped session for thread safety
Session = scoped_session(SessionFactory)

def init_db():
    """Initialize the database by creating all tables."""
    try:
        Base.metadata.create_all(engine)
        logger.info("Database tables created successfully")
    except SQLAlchemyError as e:
        logger.critical(f"Failed to create database tables: {e}")
        raise

def get_session():
    """Get a database session."""
    session = Session()
    try:
        yield session
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session.close()

async def get_user(telegram_id, session=None):
    """Get a user by Telegram ID, creating if not exists."""
    from models import User
    
    close_session = False
    if session is None:
        session = Session()
        close_session = True
    
    try:
        user = session.query(User).filter(User.telegram_id == telegram_id).first()
        if not user:
            user = User(telegram_id=telegram_id)
            session.add(user)
            session.commit()
        return user
    except SQLAlchemyError as e:
        if close_session:
            session.rollback()
        logger.error(f"Error getting/creating user {telegram_id}: {e}")
        raise
    finally:
        if close_session:
            session.close()
            
async def get_group(telegram_id, title=None, session=None):
    """Get a group by Telegram ID, creating if not exists."""
    from models import Group
    
    close_session = False
    if session is None:
        session = Session()
        close_session = True
    
    try:
        group = session.query(Group).filter(Group.telegram_id == telegram_id).first()
        if not group:
            group = Group(telegram_id=telegram_id, title=title)
            session.add(group)
            session.commit()
        elif title and group.title != title:
            group.title = title
            session.commit()
        return group
    except SQLAlchemyError as e:
        if close_session:
            session.rollback()
        logger.error(f"Error getting/creating group {telegram_id}: {e}")
        raise
    finally:
        if close_session:
            session.close()

async def get_group_member(user_id, group_id, session=None):
    """Get a group member by user and group IDs, creating if not exists."""
    from models import GroupMember
    
    close_session = False
    if session is None:
        session = Session()
        close_session = True
    
    try:
        member = session.query(GroupMember).filter(
            GroupMember.user_id == user_id,
            GroupMember.group_id == group_id
        ).first()
        
        if not member:
            member = GroupMember(user_id=user_id, group_id=group_id)
            session.add(member)
            session.commit()
        return member
    except SQLAlchemyError as e:
        if close_session:
            session.rollback()
        logger.error(f"Error getting/creating group member (user: {user_id}, group: {group_id}): {e}")
        raise
    finally:
        if close_session:
            session.close()

def populate_quran_quotes():
    """Populate the database with initial Quran quotes."""
    from models import QuranQuote
    
    quotes = [
        "قال في الحديث عليه الصلاة والسلام: مَنْ قَرَأَ حَرْفًا مِنْ كِتَابِ اللَّهِ فَلَهُ بِهِ حَسَنَةٌ، وَالحَسَنَةُ بِعَشْرِ أَمْثَالِهَا، لَا أَقُولُ الم حَرْفٌ، وَلَكِنْ أَلِفٌ حَرْفٌ، وَلَامٌ حَرْفٌ، وَمِيمٌ حَرْفٌ. رواه الترمذي وهو صحيح.",
        "إِنَّ هَذَا الْقُرْآنَ يَهْدِي لِلَّتِي هِيَ أَقْوَمُ",
        "وَلَقَدْ يَسَّرْنَا الْقُرْآنَ لِلذِّكْرِ فَهَلْ مِنْ مُدَّكِرٍ",
        "كِتَابٌ أَنْزَلْنَاهُ إِلَيْكَ مُبَارَكٌ لِيَدَّبَّرُوا",
        "وَأَنْزَلْنَا إِلَيْكَ الذِّكْرَ لِتُبَيِّنَ لِلنَّاسِ مَا نُزِّلَ إِلَيْهِمْ وَلَعَلَّهُمْ يَتَفَكَّرُونَ",
        "عن النبيّ صلى الله عليه وسلم قال: المُؤْمِنُ الذي يَقْرَأُ القُرْآنَ ويَعْمَلُ بهِ كالأُتْرُجَّةِ، طَعْمُها طَيِّبٌ ورِيحُها طَيِّبٌ، والمُؤْمِنُ الذي لا يَقْرَأُ القُرْآنَ، ويَعْمَلُ بهِ كالتَّمْرَةِ طَعْمُها طَيِّبٌ ولا رِيحَ لَها، ومَثَلُ المُنافِقِ الذي يَقْرَأُ القُرْآنَ كالرَّيْحانَةِ رِيحُها طَيِّبٌ وطَعْمُها مُرٌّ، ومَثَلُ المُنافِقِ الذي لا يَقْرَأُ القُرْآنَ كالحَنْظَلَةِ، طَعْمُها مُرٌّ ورِيحُها مُرٌّ.",
        "فمن اعرض عن ذكري فان له معيشة ضنكا"
    ]
    
    session = Session()
    try:
        # Check if quotes already exist
        count = session.query(QuranQuote).count()
        if count == 0:
            # Add quotes if none exist
            for quote_text in quotes:
                quote = QuranQuote(text=quote_text)
                session.add(quote)
            session.commit()
            logger.info(f"Added {len(quotes)} Quran quotes to the database")
        else:
            logger.info(f"Quran quotes already exist in the database ({count} quotes)")
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error populating Quran quotes: {e}")
    finally:
        session.close() 