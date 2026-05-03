from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Numeric, String, create_engine, func, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from connect import DATABASE_URL_WAREHOUSE


class Base(DeclarativeBase):
    pass


class DimProduct(Base):
    __tablename__ = "dim_products"
    __table_args__ = {"schema": "analytics"}

    product_key: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    product_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    product_category_name: Mapped[str | None] = mapped_column(String(128))
    product_category_name_english: Mapped[str | None] = mapped_column(String(128))

    def __repr__(self) -> str:
        return (
            f"DimProduct(product_key={self.product_key}, product_id={self.product_id!r}, "
            f"category={self.product_category_name_english!r})"
        )


class FactSale(Base):
    __tablename__ = "facts_sales"
    __table_args__ = {"schema": "analytics"}

    sales_key: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    order_id: Mapped[str] = mapped_column(String(64), nullable=False)
    order_item_id: Mapped[int]
    product_key: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("analytics.dim_products.product_key"), nullable=False
    )
    order_purchase_timestamp: Mapped[datetime | None] = mapped_column(DateTime)
    price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    freight_value: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    revenue: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))


class FactReview(Base):
    __tablename__ = "facts_reviews"
    __table_args__ = {"schema": "analytics"}

    review_key: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    review_id: Mapped[str | None] = mapped_column(String(64))
    order_id: Mapped[str | None] = mapped_column(String(64))
    product_key: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("analytics.dim_products.product_key"), nullable=True
    )
    review_score: Mapped[int | None]
    review_comment_message: Mapped[str | None]
    review_creation_date: Mapped[datetime | None] = mapped_column(DateTime)
    linked_to_product: Mapped[bool] = mapped_column(Boolean, nullable=False)

    def __repr__(self) -> str:
        return (
            f"FactReview(review_key={self.review_key}, review_id={self.review_id!r}, "
            f"score={self.review_score}, linked={self.linked_to_product})"
        )


if __name__ == "__main__":
    # psycopg3 requires the +psycopg dialect prefix in SQLAlchemy
    _url = DATABASE_URL_WAREHOUSE.replace("postgresql://", "postgresql+psycopg://", 1)
    engine = create_engine(_url, future=True)

    Base.metadata.create_all(engine)
    print("create_all: OK (первый запуск)")

    Base.metadata.create_all(engine)
    print("create_all: OK (повторный запуск — идемпотентность подтверждена)")

    with Session(engine) as session:
        products = session.scalars(
            select(DimProduct).order_by(DimProduct.product_key).limit(5)
        ).all()
        print(f"\nRead — первые 5 записей DimProduct:")
        for p in products:
            print(f"  {p}")

        sale_count = session.scalar(select(func.count()).select_from(FactSale))
        print(f"\nCount — строк в FactSale: {sale_count}")

        test_review = FactReview(
            review_id="ORM_TEST",
            review_score=5,
            linked_to_product=False,
        )
        session.add(test_review)
        session.commit()
        print("\nInsert — тестовая запись добавлена")

        inserted = session.scalar(
            select(FactReview).where(FactReview.review_id == "ORM_TEST")
        )
        print(f"Verify — найдена запись: {inserted}")

        session.delete(inserted)
        session.commit()
        print("Delete — тестовая запись удалена")
