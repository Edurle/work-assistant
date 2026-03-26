"""提醒模块测试"""

import pytest
from pathlib import Path
import tempfile
import os
from datetime import datetime, timedelta

# 添加src到路径
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from reminder.models import Reminder, ReminderType, IntervalUnit
from core.database import Database


class TestReminder:
    """提醒测试"""

    def test_create_point_reminder(self):
        """测试创建时间点提醒"""
        reminder = Reminder(
            title="测试提醒",
            content="这是测试内容",
            reminder_type=ReminderType.POINT,
            trigger_time=datetime.now() + timedelta(hours=1)
        )

        assert reminder.title == "测试提醒"
        assert reminder.reminder_type == ReminderType.POINT
        assert reminder.trigger_time is not None

    def test_create_interval_reminder(self):
        """测试创建间隔提醒"""
        reminder = Reminder(
            title="间隔提醒",
            reminder_type=ReminderType.INTERVAL,
            interval_value=30,
            interval_unit=IntervalUnit.MINUTES,
            is_recurring=True
        )

        assert reminder.reminder_type == ReminderType.INTERVAL
        assert reminder.interval_value == 30
        assert reminder.is_recurring == True

    def test_calculate_next_trigger_point(self):
        """测试计算下次触发时间（时间点）"""
        trigger_time = datetime.now() + timedelta(hours=1)
        reminder = Reminder(
            title="测试",
            reminder_type=ReminderType.POINT,
            trigger_time=trigger_time
        )

        next_trigger = reminder.calculate_next_trigger()
        assert next_trigger == trigger_time

    def test_calculate_next_trigger_interval(self):
        """测试计算下次触发时间（间隔）"""
        reminder = Reminder(
            title="测试",
            reminder_type=ReminderType.INTERVAL,
            interval_value=30,
            interval_unit=IntervalUnit.MINUTES
        )

        next_trigger = reminder.calculate_next_trigger()
        assert next_trigger is not None

        # 下次触发应该在未来
        assert next_trigger > datetime.now()

    def test_is_time_to_trigger(self):
        """测试是否到触发时间"""
        # 过去的提醒
        past_reminder = Reminder(
            title="过去",
            reminder_type=ReminderType.POINT,
            next_trigger=datetime.now() - timedelta(minutes=1)
        )
        assert past_reminder.is_time_to_trigger() == True

        # 未来的提醒
        future_reminder = Reminder(
            title="未来",
            reminder_type=ReminderType.POINT,
            next_trigger=datetime.now() + timedelta(hours=1)
        )
        assert future_reminder.is_time_to_trigger() == False

        # 禁用的提醒
        disabled_reminder = Reminder(
            title="禁用",
            reminder_type=ReminderType.POINT,
            is_enabled=False,
            next_trigger=datetime.now() - timedelta(minutes=1)
        )
        assert disabled_reminder.is_time_to_trigger() == False

    def test_to_dict(self):
        """测试转换为字典"""
        reminder = Reminder(
            id=1,
            title="测试",
            content="内容",
            reminder_type=ReminderType.POINT
        )

        d = reminder.to_dict()
        assert d['id'] == 1
        assert d['title'] == "测试"
        assert d['reminder_type'] == "point"


class TestReminderScheduler:
    """提醒调度器测试"""

    @pytest.fixture
    def setup_scheduler(self):
        """设置调度器"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        Database._instance = None
        db = Database(db_path)

        from reminder.scheduler import ReminderScheduler
        scheduler = ReminderScheduler(db)

        yield scheduler

        if os.path.exists(db_path):
            os.unlink(db_path)

    def test_add_reminder(self, setup_scheduler):
        """测试添加提醒"""
        scheduler = setup_scheduler

        reminder = Reminder(
            title="测试提醒",
            content="测试内容",
            reminder_type=ReminderType.POINT,
            trigger_time=datetime.now() + timedelta(hours=1)
        )

        reminder_id = scheduler.add_reminder(reminder)
        assert reminder_id is not None

        # 验证添加
        reminders = scheduler.get_all_reminders()
        assert len(reminders) > 0

    def test_remove_reminder(self, setup_scheduler):
        """测试删除提醒"""
        scheduler = setup_scheduler

        reminder = Reminder(
            title="要删除的提醒",
            reminder_type=ReminderType.POINT,
            trigger_time=datetime.now() + timedelta(hours=1)
        )

        reminder_id = scheduler.add_reminder(reminder)
        assert reminder_id is not None

        # 删除
        result = scheduler.remove_reminder(reminder_id)
        assert result == True

        # 验证删除
        r = scheduler.get_reminder(reminder_id)
        assert r is None

    def test_toggle_enabled(self, setup_scheduler):
        """测试切换启用状态"""
        scheduler = setup_scheduler

        reminder = Reminder(
            title="测试",
            reminder_type=ReminderType.POINT,
            trigger_time=datetime.now() + timedelta(hours=1)
        )

        reminder_id = scheduler.add_reminder(reminder)

        # 切换
        result = scheduler.toggle_enabled(reminder_id)
        assert result == True

        # 验证状态
        r = scheduler.get_reminder(reminder_id)
        assert r.is_enabled == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
