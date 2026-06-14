from datetime import datetime

from fastapi import HTTPException, status

from app.models import Appointment, AppointmentStatus, STUDENT_TAG_HINTS, StudentTag
from app.schemas import AppointmentCreate, AppointmentHint, AppointmentRead
from app.store import appointments, cancel_rule, coaches, next_id, students


def _build_student_hints(student_id: int) -> tuple[list[str], list[AppointmentHint]]:
    student = students[student_id]
    tag_values = [t.value for t in student.tags]
    hints: list[AppointmentHint] = []
    for tag in student.tags:
        hint_msg = STUDENT_TAG_HINTS.get(tag)
        if hint_msg:
            level = "warning" if tag in (StudentTag.makeup, StudentTag.follow_up) else "info"
            hints.append(
                AppointmentHint(
                    type="student_tag",
                    message=hint_msg,
                    tag=tag,
                    level=level,
                )
            )
    if student.remaining_hours <= 5:
        hints.append(
            AppointmentHint(
                type="low_hours",
                message=f"该学员剩余课时不足（仅剩 {student.remaining_hours}h），请提醒学员及时续费",
                level="danger",
            )
        )
    return tag_values, hints


def appointment_to_read(appointment: Appointment) -> AppointmentRead:
    student = students[appointment.student_id]
    coach = coaches[appointment.coach_id]
    tag_values, hints = _build_student_hints(appointment.student_id)
    return AppointmentRead(
        id=appointment.id,
        student_id=student.id,
        student_name=student.name,
        student_tags=tag_values,
        coach_id=coach.id,
        coach_name=coach.name,
        start_time=appointment.start_time,
        end_time=appointment.end_time,
        status=appointment.status,
        created_at=appointment.created_at,
        cancelled_at=appointment.cancelled_at,
        cancel_reason=appointment.cancel_reason,
        hints=hints,
    )


def list_appointments(status_filter: AppointmentStatus | None = None) -> list[AppointmentRead]:
    values = sorted(appointments.values(), key=lambda item: item.start_time)
    if status_filter:
        values = [item for item in values if item.status == status_filter]
    return [appointment_to_read(item) for item in values]


def create_appointment(payload: AppointmentCreate) -> AppointmentRead:
    if payload.student_id not in students:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Student not found")
    if payload.coach_id not in coaches or not coaches[payload.coach_id].active:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Active coach not found")
    start_time = _as_naive(payload.start_time)
    end_time = _as_naive(payload.end_time)
    student = students[payload.student_id]

    if start_time <= datetime.now():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cannot book a past time slot")

    active_count = sum(
        1
        for item in appointments.values()
        if item.student_id == payload.student_id and item.status == AppointmentStatus.booked
    )

    max_bookings = cancel_rule.max_active_bookings_per_student
    if StudentTag.beginner in student.tags:
        max_bookings = max(1, max_bookings - 1)
    if StudentTag.makeup in student.tags:
        max_bookings = max_bookings + 1

    if active_count >= max_bookings:
        tag_msg = ""
        if StudentTag.beginner in student.tags:
            tag_msg = "（新手学员最多允许 2 个进行中的预约）"
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Student has reached active booking limit{tag_msg}",
        )

    has_conflict = any(
        item.status == AppointmentStatus.booked
        and item.coach_id == payload.coach_id
        and start_time < item.end_time
        and end_time > item.start_time
        for item in appointments.values()
    )
    if has_conflict:
        raise HTTPException(status.HTTP_409_CONFLICT, "Coach already has a booking in this time slot")

    duration_hours = (end_time - start_time).total_seconds() / 3600

    if StudentTag.beginner in student.tags and duration_hours > 2:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "新手学员单次预约时长不得超过 2 小时，请分时段预约",
        )
    if StudentTag.slow_learner in student.tags and duration_hours > 3:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "需要多加练习的学员单次预约时长不得超过 3 小时，以保证学习效果",
        )

    if student.remaining_hours < duration_hours:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Student does not have enough remaining hours")

    appointment = Appointment(
        id=next_id("appointment"),
        student_id=payload.student_id,
        coach_id=payload.coach_id,
        start_time=start_time,
        end_time=end_time,
        created_at=datetime.now(),
    )
    appointments[appointment.id] = appointment
    return appointment_to_read(appointment)


def _as_naive(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone().replace(tzinfo=None)


def cancel_appointment(appointment_id: int, reason: str) -> AppointmentRead:
    appointment = appointments.get(appointment_id)
    if not appointment:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Appointment not found")
    if appointment.status == AppointmentStatus.cancelled:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Appointment already cancelled")
    if appointment.status == AppointmentStatus.completed and not cancel_rule.allow_cancel_completed:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Completed appointments cannot be cancelled")

    hours_before_start = (appointment.start_time - datetime.now()).total_seconds() / 3600
    if hours_before_start < cancel_rule.min_hours_before_start:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Appointments must be cancelled at least {cancel_rule.min_hours_before_start} hours in advance",
        )

    appointment.status = AppointmentStatus.cancelled
    appointment.cancelled_at = datetime.now()
    appointment.cancel_reason = reason
    appointments[appointment.id] = appointment
    return appointment_to_read(appointment)
