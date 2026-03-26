"""提醒数据模型"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from enum import Enum


class ReminderType(Enum):
    """提醒类型"""
    POINT = "point"        # 时间点提醒
    INTERVAL = "interval"  # 间隔提醒


class IntervalUnit(Enum):
    """间隔单位"""
    SECONDS = "seconds"
    MINUTES = "minutes"
    HOURS = "hours"
    DAYS = "days"


@dataclass
class Reminder:
    """提醒数据类"""
    id: Optional[int] = None
    title: str = ""
    content: str = ""
    reminder_type: ReminderType = ReminderType.POINT
    trigger_time: Optional[datetime] = None
    interval_value: int = 1
    interval_unit: IntervalUnit = IntervalUnit.MINUTES
    is_recurring: bool = False
    is_enabled: bool = True
    next_trigger: Optional[datetime] = None
    sound_enabled: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def from_db_row(cls, row: dict) -> 'Reminder':
        """从数据库行创建实例"""
        return cls(
            id=row.get('id'),
            title=row.get('title', ''),
            content=row.get('content', ''),
            reminder_type=ReminderType(row.get('reminder_type', 'point')),
            trigger_time=cls._parse_datetime(row.get('trigger_time')),
            interval_value=row.get('interval_value', 1),
            interval_unit=IntervalUnit(row.get('interval_unit', 'minutes')),
            is_recurring=bool(row.get('is_recurring', 0)),
            is_enabled=bool(row.get('is_enabled', 1)),
            next_trigger=cls._parse_datetime(row.get('next_trigger')),
            sound_enabled=bool(row.get('sound_enabled', 1)),
            created_at=cls._parse_datetime(row.get('created_at')),
            updated_at=cls._parse_datetime(row.get('updated_at')),
        )

    @staticmethod
    def _parse_datetime(value: str) -> Optional[datetime]:
        """解析日期时间"""
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace('Z', '+00:00'))
        except (ValueError, TypeError):
            return None

    def calculate_next_trigger(self) -> Optional[datetime]:
        """计算下次触发时间"""
        if self.reminder_type == ReminderType.POINT:
            return self.trigger_time
        else:
            # 间隔提醒
            delta = timedelta(**{self.interval_unit.value: self.interval_value})
            now = datetime.now()
            if self.next_trigger:
                return self.next_trigger + delta
            return now + delta

    def is_time_to_trigger(self) -> bool:
        """检查是否到触发时间"""
        if not self.is_enabled or not self.next_trigger:
            return False
        return datetime.now() >= self.next_trigger

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'reminder_type': self.reminder_type.value,
            'trigger_time': self.trigger_time.isoformat() if self.trigger_time else None,
            'interval_value': self.interval_value,
            'interval_unit': self.interval_unit.value,
            'is_recurring': self.is_recurring,
            'is_enabled': self.is_enabled,
            'next_trigger': self.next_trigger.isoformat() if self.next_trigger else None,
            'sound_enabled': self.sound_enabled,
        }


@dataclass
class ReminderLog:
    """提醒日志数据类"""
    id: Optional[int] = None
    reminder_id: int = 0
    triggered_at: Optional[datetime] = None
    status: str = "triggered"  # triggered, dismissed, snoozed

    @classmethod
    def from_db_row(cls, row: dict) -> 'ReminderLog':
        """从数据库行创建实例"""
        return cls(
            id=row.get('id'),
            reminder_id=row.get('reminder_id', 0),
            triggered_at=cls._parse_datetime(row.get('triggered_at')),
            status=row.get('status', 'triggered'),
        )

    @staticmethod
    def _parse_datetime(value: str) -> Optional[datetime]:
        """解析日期时间"""
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace('Z', '+00:00'))
        except (ValueError, TypeError):
            return None
