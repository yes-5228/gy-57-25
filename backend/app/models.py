from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class AppointmentStatus(str, Enum):
    booked = "booked"
    cancelled = "cancelled"
    completed = "completed"


class StudentTag(str, Enum):
    beginner = "新手"
    makeup = "补考"
    follow_up = "重点跟进"
    fast_learner = "学习快"
    slow_learner = "需多加练习"


STUDENT_TAG_HINTS: dict[StudentTag, str] = {
    StudentTag.beginner: "该学员为新手，建议安排耐心细致的教练，初次预约请预留充足时间",
    StudentTag.makeup: "该学员需要补考，建议重点辅导薄弱环节，预约时优先安排经验丰富的教练",
    StudentTag.follow_up: "该学员需要重点跟进，建议教练提前了解学员学习进度，课后及时反馈",
    StudentTag.fast_learner: "该学员学习进度较快，可适当加快教学节奏",
    StudentTag.slow_learner: "该学员需要多加练习，建议教练耐心指导，合理安排课时进度",
}


STUDENT_TAG_COLORS: dict[StudentTag, str] = {
    StudentTag.beginner: "#3b82f6",
    StudentTag.makeup: "#ef4444",
    StudentTag.follow_up: "#f59e0b",
    StudentTag.fast_learner: "#10b981",
    StudentTag.slow_learner: "#8b5cf6",
}


class Student(BaseModel):
    id: int
    name: str
    phone: str
    remaining_hours: int = Field(ge=0)
    tags: list[StudentTag] = Field(default_factory=list)


class Coach(BaseModel):
    id: int
    name: str
    phone: str
    car_no: str
    specialties: list[str]
    active: bool = True


class Appointment(BaseModel):
    id: int
    student_id: int
    coach_id: int
    start_time: datetime
    end_time: datetime
    status: AppointmentStatus = AppointmentStatus.booked
    created_at: datetime
    cancelled_at: datetime | None = None
    cancel_reason: str | None = None


class CancelRule(BaseModel):
    min_hours_before_start: int = 2
    max_active_bookings_per_student: int = 3
    allow_cancel_completed: bool = False
