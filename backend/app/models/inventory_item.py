from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, func
from app.database import Base


class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    part_number = Column(String(100))
    description = Column(String(200))
    category = Column(String(100))  # fan_blade, turbine_disk, combustor_liner, etc.
    work_order = Column(String(100))
    status = Column(String(50))  # in_process, awaiting_inspection, complete, shipped
    is_itar = Column(Boolean, default=False)
    tag_id = Column(Integer, ForeignKey("tags.id"))
    created_at = Column(DateTime, server_default=func.now())
