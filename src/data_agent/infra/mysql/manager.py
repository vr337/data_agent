"""
MySql管理模块
"""

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from data_agent.core.configs.app_config import DBConfig, app_config


class MySqlClientManager:
    """MySql上下文管理器"""

    def __init__(self, config: DBConfig):
        self._config = config
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None

    @property
    def _db_url(self) -> str:
        return f"mysql+asyncmy://{self._config.user}:{self._config.password}@{self._config.host}:{self._config.port}/{self._config.database}?charset=utf8mb4"

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        if self._session_factory is None:
            raise RuntimeError("请先调用init_db方法进行初始化")
        return self._session_factory

    def init_db(self) -> None:
        """初始化数据库连接"""
        # 1.创建MySql引擎
        if self._engine is None:
            self._engine = create_async_engine(
                url=self._db_url,
                echo=False,
                pool_size=10,  # 数据库连接池的常驻连接数(连接结束后只会归还，可复用连接)
                max_overflow=5,  # 数据库连接池的临时连接数，当常驻连接全部被使用，那么会使用临时连接数(连接结束后会销毁连接，每次使用都会重新创建)
            )
        # 2.创建会话工厂
        if self._session_factory is None:
            self._session_factory = async_sessionmaker(
                bind=self._engine,
                class_=AsyncSession,
                autoflush=False,  # 关闭自动刷新，如果开启，虽然会提升查询效率，查询的数据会放到暂存区，但新增且未提交的数据也会放到暂存取，导致在同一个事务，可以读到未提交是数据，综合考虑，关闭
                autobegin=True,  # 开启事务自动开启
            )

    async def close(self) -> None:
        """关闭数据库连接"""
        # 1.关闭引擎
        if self._engine is not None:
            await self._engine.dispose()
            # 2.将engin和session_factory置为None
            self._engine = None
            self._session_factory = None


_dw_mysql_manager: MySqlClientManager | None = None
_meta_mysql_manager: MySqlClientManager | None = None


def get_dw_mysql_manager() -> MySqlClientManager:
    global _dw_mysql_manager
    if _dw_mysql_manager is None:
        _dw_mysql_manager = MySqlClientManager(app_config.db_dw)
    return _dw_mysql_manager


def get_meta_mysql_manager() -> MySqlClientManager:
    global _meta_mysql_manager
    if _meta_mysql_manager is None:
        _meta_mysql_manager = MySqlClientManager(app_config.db_meta)
    return _meta_mysql_manager
