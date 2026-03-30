"""提醒调度模块"""

from PySide6.QtCore import QObject, QTimer, Signal
from typing import List, Optional
from datetime import datetime
from loguru import logger

from .models import Reminder, ReminderLog, ReminderType


class ReminderScheduler(QObject):
    """提醒调度器"""

    # 信号：提醒触发
    reminder_triggered = Signal(object)  # Reminder

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.reminders: List[Reminder] = []
        self.check_timer = QTimer(self)
        self.check_timer.timeout.connect(self._check_reminders)
        self.check_interval = 1000  # 1秒检查一次
        logger.debug("提醒调度器初始化完成")

    def start(self):
        """启动调度器"""
        self._load_reminders()
        self._skip_missed_reminders()  # 跳过错过的提醒
        self.check_timer.start(self.check_interval)
        logger.info(f"提醒调度器已启动，当前有 {len(self.reminders)} 个活跃提醒")

    def _skip_missed_reminders(self):
        """跳过错过的间隔提醒，将 next_trigger 更新到下一个未来时间点"""
        from datetime import timedelta

        now = datetime.now()
        for reminder in self.reminders:
            if reminder.reminder_type == ReminderType.INTERVAL and reminder.next_trigger:
                if reminder.next_trigger < now:
                    # 计算间隔秒数
                    interval_seconds = self._get_interval_seconds(reminder)
                    if interval_seconds > 0:
                        # 计算需要跳过多少个间隔才能到达未来时间点
                        missed_seconds = (now - reminder.next_trigger).total_seconds()
                        skip_intervals = int(missed_seconds / interval_seconds) + 1
                        new_trigger = reminder.next_trigger + timedelta(seconds=skip_intervals * interval_seconds)

                        # 更新内存和数据库
                        reminder.next_trigger = new_trigger
                        self.db.update(
                            'reminders',
                            {'next_trigger': new_trigger.isoformat()},
                            'id = ?',
                            (reminder.id,)
                        )
                        logger.info(f"跳过提醒 [{reminder.title}] 的 {skip_intervals} 次触发，下次触发时间: {new_trigger}")

    def _get_interval_seconds(self, reminder: Reminder) -> int:
        """获取间隔秒数"""
        unit_map = {
            'seconds': 1,
            'minutes': 60,
            'hours': 3600,
            'days': 86400,
        }
        return reminder.interval_value * unit_map.get(reminder.interval_unit.value, 0)

    def stop(self):
        """停止调度器"""
        self.check_timer.stop()
        logger.info("提醒调度器已停止")

    def _load_reminders(self):
        """从数据库加载启用的提醒"""
        rows = self.db.fetchall(
            "SELECT * FROM reminders WHERE is_enabled = 1 ORDER BY next_trigger ASC"
        )
        self.reminders = [Reminder.from_db_row(row) for row in rows]

    def reload(self):
        """重新加载提醒"""
        self._load_reminders()
        logger.debug(f"重新加载提醒，当前 {len(self.reminders)} 个")

    def add_reminder(self, reminder: Reminder) -> Optional[int]:
        """添加提醒"""
        try:
            # 计算下次触发时间
            reminder.next_trigger = reminder.calculate_next_trigger()

            reminder_id = self.db.insert('reminders', {
                'title': reminder.title,
                'content': reminder.content,
                'reminder_type': reminder.reminder_type.value,
                'trigger_time': reminder.trigger_time.isoformat() if reminder.trigger_time else None,
                'interval_value': reminder.interval_value,
                'interval_unit': reminder.interval_unit.value,
                'is_recurring': int(reminder.is_recurring),
                'is_enabled': int(reminder.is_enabled),
                'next_trigger': reminder.next_trigger.isoformat() if reminder.next_trigger else None,
                'sound_enabled': int(reminder.sound_enabled),
            })

            reminder.id = reminder_id
            if reminder.is_enabled:
                self.reminders.append(reminder)

            logger.info(f"添加提醒: ID={reminder_id}, 标题={reminder.title}")
            return reminder_id

        except Exception as e:
            logger.error(f"添加提醒失败: {e}")
            return None

    def update_reminder(self, reminder: Reminder) -> bool:
        """更新提醒"""
        try:
            reminder.next_trigger = reminder.calculate_next_trigger()

            self.db.update(
                'reminders',
                {
                    'title': reminder.title,
                    'content': reminder.content,
                    'reminder_type': reminder.reminder_type.value,
                    'trigger_time': reminder.trigger_time.isoformat() if reminder.trigger_time else None,
                    'interval_value': reminder.interval_value,
                    'interval_unit': reminder.interval_unit.value,
                    'is_recurring': int(reminder.is_recurring),
                    'is_enabled': int(reminder.is_enabled),
                    'next_trigger': reminder.next_trigger.isoformat() if reminder.next_trigger else None,
                    'sound_enabled': int(reminder.sound_enabled),
                    'updated_at': datetime.now().isoformat(),
                },
                'id = ?',
                (reminder.id,)
            )

            # 更新内存中的提醒
            for i, r in enumerate(self.reminders):
                if r.id == reminder.id:
                    if reminder.is_enabled:
                        self.reminders[i] = reminder
                    else:
                        self.reminders.pop(i)
                    break
            else:
                if reminder.is_enabled:
                    self.reminders.append(reminder)

            logger.debug(f"更新提醒: ID={reminder.id}")
            return True

        except Exception as e:
            logger.error(f"更新提醒失败: {e}")
            return False

    def remove_reminder(self, reminder_id: int) -> bool:
        """删除提醒"""
        try:
            self.db.delete('reminders', 'id = ?', (reminder_id,))
            self.reminders = [r for r in self.reminders if r.id != reminder_id]
            logger.info(f"删除提醒: ID={reminder_id}")
            return True
        except Exception as e:
            logger.error(f"删除提醒失败: {e}")
            return False

    def toggle_enabled(self, reminder_id: int) -> bool:
        """切换启用状态"""
        try:
            reminder = next((r for r in self.reminders if r.id == reminder_id), None)
            if reminder:
                reminder.is_enabled = not reminder.is_enabled
                self.db.update(
                    'reminders',
                    {'is_enabled': int(reminder.is_enabled), 'updated_at': datetime.now().isoformat()},
                    'id = ?',
                    (reminder_id,)
                )

                if not reminder.is_enabled:
                    self.reminders = [r for r in self.reminders if r.id != reminder_id]
                else:
                    self.reminders.append(reminder)

                return True
            return False
        except Exception as e:
            logger.error(f"切换提醒状态失败: {e}")
            return False

    def get_all_reminders(self) -> List[Reminder]:
        """获取所有提醒"""
        rows = self.db.fetchall("SELECT * FROM reminders ORDER BY next_trigger ASC")
        return [Reminder.from_db_row(row) for row in rows]

    def get_reminder(self, reminder_id: int) -> Optional[Reminder]:
        """获取单个提醒"""
        row = self.db.fetchone("SELECT * FROM reminders WHERE id = ?", (reminder_id,))
        return Reminder.from_db_row(row) if row else None

    def _check_reminders(self):
        """检查是否有需要触发的提醒"""
        now = datetime.now()

        for reminder in self.reminders[:]:  # 使用切片创建副本以安全删除
            if reminder.is_time_to_trigger():
                self._trigger_reminder(reminder)

    def _trigger_reminder(self, reminder: Reminder):
        """触发提醒"""
        logger.info(f"触发提醒: ID={reminder.id}, 标题={reminder.title}")

        # 发送信号
        self.reminder_triggered.emit(reminder)

        # 记录日志
        self._log_trigger(reminder)

        # 更新下次触发时间
        if reminder.reminder_type == ReminderType.INTERVAL:
            reminder.next_trigger = reminder.calculate_next_trigger()
            self.db.update(
                'reminders',
                {'next_trigger': reminder.next_trigger.isoformat()},
                'id = ?',
                (reminder.id,)
            )
        elif reminder.reminder_type == ReminderType.POINT:
            # 单次提醒，禁用
            reminder.is_enabled = False
            self.db.update(
                'reminders',
                {'is_enabled': 0, 'updated_at': datetime.now().isoformat()},
                'id = ?',
                (reminder.id,)
            )
            self.reminders = [r for r in self.reminders if r.id != reminder.id]

    def _log_trigger(self, reminder: Reminder):
        """记录触发日志"""
        try:
            self.db.insert('reminder_logs', {
                'reminder_id': reminder.id,
                'status': 'triggered',
            })
        except Exception as e:
            logger.error(f"记录提醒日志失败: {e}")

    def get_trigger_history(self, reminder_id: int, limit: int = 10) -> List[ReminderLog]:
        """获取提醒触发历史"""
        rows = self.db.fetchall(
            "SELECT * FROM reminder_logs WHERE reminder_id = ? ORDER BY triggered_at DESC LIMIT ?",
            (reminder_id, limit)
        )
        return [ReminderLog.from_db_row(row) for row in rows]

    def snooze_reminder(self, reminder_id: int, minutes: int = 5) -> bool:
        """贪睡提醒"""
        try:
            from datetime import timedelta
            next_trigger = datetime.now() + timedelta(minutes=minutes)

            self.db.update(
                'reminders',
                {'next_trigger': next_trigger.isoformat()},
                'id = ?',
                (reminder_id,)
            )

            for r in self.reminders:
                if r.id == reminder_id:
                    r.next_trigger = next_trigger
                    break

            logger.debug(f"贪睡提醒: ID={reminder_id}, {minutes}分钟后")
            return True

        except Exception as e:
            logger.error(f"贪睡提醒失败: {e}")
            return False
