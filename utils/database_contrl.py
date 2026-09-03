from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine,AsyncSession
from crud import inquiry
import os
from dotenv import load_dotenv

# 登录配置文件
config = inquiry.load_config("./config/config.yml")

# 获取数据库相关配置
database_config = config.get("database")
# 当配置文件没有配置时，从.env文件中获取配置
if database_config is None:
    load_dotenv(".env")
    database_url = os.getenv("DATABASE_URL")
    echo =os.getenv("ECHO").lower() == "true"
    pool_size=int(os.getenv("POOL_SIZE"))
    max_overflow=int(os.getenv("MAX_OVERFLOW"))
else:
    database_url = database_config["database_url"]
    echo = database_config["echo"]
    pool_size = database_config["pool_size"]
    max_overflow = database_config["max_overflow"]

engine = create_async_engine(
    url=database_url,
    echo=echo,
    pool_size=pool_size,
    max_overflow=max_overflow,
)

session_orm = sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)

async def get_db():
    async with session_orm() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()