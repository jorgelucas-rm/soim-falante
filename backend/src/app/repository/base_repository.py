from abc import ABC, abstractmethod
from typing import Any, Generic, Optional, Type, TypeVar

from fastapi import Depends
from sqlalchemy import Boolean, asc, desc, or_
from sqlalchemy.orm import Query, Session
from src.infra.storage import get_session

T = TypeVar("T")
Trepo = TypeVar("Trepo", bound="BaseRepository")


class BaseRepository(Generic[T], ABC):
    """Repositório base genérico com suporte a paginação, filtros e ordenação."""

    def __init__(self, session: Session):
        """Inicializa o repositório com a sessão do banco de dados."""
        self.session = session

    @property
    @abstractmethod
    def model(self) -> Type[T]:
        """Deve retornar o modelo SQLAlchemy da entidade."""
        pass

    @classmethod
    def get_instance(cls: Type[Trepo]):
        """Retorna uma factory function para injeção de dependência via FastAPI."""

        def _get_repo(
            session: Session = Depends(get_session),
        ) -> Trepo:
            return cls(session=session)

        return _get_repo

    @property
    def orderable_fields(self) -> dict:
        """Colunas permitidas para ordenação."""
        return {}

    @property
    def equal_filters(self) -> dict:
        """Mapeamento de campos para filtros por igualdade (column == value)."""
        return {}

    @property
    def like_filters(self) -> dict:
        """Mapeamento de campos para filtros por similaridade (column ILIKE %value%)."""
        return {}

    def _cast_value(self, column, value):
        """Converte valores de string para tipo correto"""
        if isinstance(column.type, Boolean):
            return str(value).lower() in ("true", "1", "yes")
        return value

    def _apply_order(
        self,
        query: Query,
        order_by: str | None = None,
        order_direction: str | None = None,
    ) -> Query:
        """
        Aplica ordenação segura em uma query SQLAlchemy.

        - order_by: chave do campo a ordenar (deve estar em `orderable_fields`)
        - order_direction: 'asc' ou 'desc' (default 'asc')
        """
        if not order_direction:
            order_direction = "asc"

        if order_by and order_by in self.orderable_fields:
            column = self.orderable_fields[order_by]

        elif self.orderable_fields:
            column = next(iter(self.orderable_fields.values()))

        else:
            return query

        if order_direction.lower() == "desc":
            query = query.order_by(desc(column))

        else:
            query = query.order_by(asc(column))

        return query

    def _apply_filters(
        self,
        query: Query,
        filters: dict | None = None,
    ) -> Query:
        """
        Aplica filtros LIKE e EQUAL em uma query SQLAlchemy
        - query: query base
        - filters: dict de filtros {campo: valor}
        """
        if not filters:
            return query

        like_conditions = []
        for field, value in filters.items():
            if field in self.like_filters:
                column = self.like_filters[field]
                if isinstance(value, (list, tuple, set)):
                    for v in value:
                        like_conditions.append(column.ilike(f"%{v}%"))
                else:
                    like_conditions.append(column.ilike(f"%{value}%"))
            elif field in self.equal_filters:
                column = self.equal_filters[field]

                if isinstance(value, (list, tuple, set)):
                    casted_values = [self._cast_value(column, v) for v in value]
                    query = query.filter(column.in_(casted_values))
                else:
                    query = query.filter(column == self._cast_value(column, value))

        if like_conditions:
            query = query.filter(or_(*like_conditions))

        return query

    def _paginate(
        self,
        base_query: Query,
        page: int = 1,
        page_size: int = 10,
        order_by: str | None = None,
        order_direction: str | None = None,
        filters: dict | None = None,
    ) -> tuple[list[T], int, int]:
        """Aplica filtros, ordenação e paginação em uma query base; retorna (itens, total, total_filtrado)."""
        query_with_filters = self._apply_filters(query=base_query, filters=filters)
        query_with_order = self._apply_order(
            query=query_with_filters,
            order_by=order_by,
            order_direction=order_direction,
        )
        total = base_query.count()
        total_filtered = query_with_filters.count() if filters else total
        items = query_with_order.limit(page_size).offset((page - 1) * page_size).all()
        return items, total, total_filtered

    def get_paginated(
        self,
        page: int = 1,
        page_size: int = 10,
        order_by: str | None = None,
        order_direction: str | None = None,
        filters: dict | None = None,
    ) -> tuple[list[T], int, int]:
        """Retorna página de registros do modelo com suporte a filtros e ordenação."""
        base_query = self.session.query(self.model)
        return self._paginate(
            base_query, page, page_size, order_by, order_direction, filters
        )

    def get_by_pk(self, pk: Any) -> Optional[T]:
        """Retorna a entidade pelo seu identificador primário, ou None se não encontrada."""
        return self.session.get(entity=self.model, ident=pk)

    def save(self, entity: T) -> T:
        """Persiste a entidade (insert ou update) e retorna a instância atualizada."""
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)

        return entity

    def delete(self, entity: T) -> None:
        """Remove a entidade do banco de dados."""
        self.session.delete(entity)
        self.session.commit()
