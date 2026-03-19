"""프로젝트/솔루션/계정과목 마스터 Repository - 공통 BaseMasterRepository 기반"""
import logging
from typing import Any

from app.database.base import PgRepository

logger = logging.getLogger(__name__)


class BaseMasterRepository(PgRepository):
    """마스터 테이블 공통 CRUD. select_fields, key_field로 테이블별 차이 흡수"""

    allowed_update_fields = {"name", "active_yn", "sort_order"}

    def __init__(
        self,
        table_name: str,
        key_field: str,
        select_fields: tuple[str, ...],
        expose_name_as_id: bool = False,
    ):
        super().__init__()
        self.table_name = table_name
        self.key_field = key_field
        self.select_fields = select_fields
        self.expose_name_as_id = expose_name_as_id

    def get_all(self, active_only: bool = False) -> list[dict[str, Any]]:
        fields = ", ".join(self.select_fields)
        sql = f"SELECT {fields} FROM {self.table_name}"
        params: list[Any] = []

        if active_only:
            sql += " WHERE active_yn = TRUE"

        sql += " ORDER BY sort_order, name"

        try:
            rows = self.fetch_all(sql, params if params else None)
        except Exception as e:
            logger.exception("%s get_all 실패: %s", self.table_name, e)
            return []

        if self.expose_name_as_id:
            for row in rows:
                row["id"] = row["name"]
        return rows

    def create(
        self, name: str, active_yn: bool = True, sort_order: int = 0
    ) -> dict[str, Any] | None:
        fields = ", ".join(self.select_fields)
        sql = f"""
            INSERT INTO {self.table_name} (name, active_yn, sort_order)
            VALUES (%s, %s, %s)
            RETURNING {fields}
        """
        row = self.fetch_one(sql, (name, active_yn, sort_order))
        if row and self.expose_name_as_id:
            row["id"] = row["name"]
        return row

    def update(
        self, key_value: Any, data: dict[str, Any]
    ) -> dict[str, Any] | None:
        updates = []
        params = []

        for key, value in data.items():
            if key in self.allowed_update_fields and value is not None:
                updates.append(f"{key} = %s")
                params.append(value)

        if not updates:
            for row in self.get_all():
                if row[self.key_field] == key_value:
                    return row
            return None

        fields = ", ".join(self.select_fields)
        params.append(key_value)

        sql = f"""
            UPDATE {self.table_name}
               SET {", ".join(updates)}
             WHERE {self.key_field} = %s
         RETURNING {fields}
        """
        row = self.fetch_one(sql, params)
        if row and self.expose_name_as_id:
            row["id"] = row["name"]
        return row

    def delete(self, key_value: Any) -> bool:
        deleted = self.execute(
            f"DELETE FROM {self.table_name} WHERE {self.key_field} = %s",
            (key_value,),
        )
        return deleted > 0


class ProjectRepository(BaseMasterRepository):
    """PROJECTS 테이블. id SERIAL 있으나 API는 name을 식별자로 사용"""

    def __init__(self):
        super().__init__(
            table_name='"PROJECTS"',
            key_field="name",
            select_fields=("name", "active_yn", "sort_order"),
            expose_name_as_id=True,
        )


class SolutionRepository(BaseMasterRepository):
    """SOLUTIONS 테이블. id SERIAL PRIMARY KEY 사용"""

    def __init__(self):
        super().__init__(
            table_name='"SOLUTIONS"',
            key_field="id",
            select_fields=("id", "name", "active_yn", "sort_order"),
            expose_name_as_id=False,
        )


class AccountSubjectRepository(BaseMasterRepository):
    """EXPENSE_CATEGORIES 테이블. id SERIAL 있으나 API는 name을 식별자로 사용"""

    def __init__(self):
        super().__init__(
            table_name='"EXPENSE_CATEGORIES"',
            key_field="name",
            select_fields=("name", "active_yn", "sort_order"),
            expose_name_as_id=True,
        )
