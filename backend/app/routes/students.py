from fastapi import APIRouter, HTTPException, status

from app.models import Student, StudentTag, STUDENT_TAG_HINTS
from app.schemas import AppointmentHint, StudentCreate, StudentRead, StudentTagsUpdate
from app.store import next_id, students

router = APIRouter()


@router.get("", response_model=list[StudentRead])
def list_students(tag: StudentTag | None = None) -> list[Student]:
    result = list(students.values())
    if tag:
        result = [s for s in result if tag in s.tags]
    return result


@router.post("", response_model=StudentRead, status_code=201)
def create_student(payload: StudentCreate) -> Student:
    student = Student(id=next_id("student"), **payload.model_dump())
    students[student.id] = student
    return student


@router.get("/tags/definitions")
def list_tag_definitions() -> list[dict]:
    return [
        {
            "value": tag.value,
            "key": tag.name,
            "hint": STUDENT_TAG_HINTS.get(tag, ""),
        }
        for tag in StudentTag
    ]


@router.get("/{student_id}", response_model=StudentRead)
def get_student(student_id: int) -> Student:
    if student_id not in students:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Student not found")
    return students[student_id]


@router.patch("/{student_id}/tags", response_model=StudentRead)
def update_student_tags(student_id: int, payload: StudentTagsUpdate) -> Student:
    if student_id not in students:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Student not found")
    student = students[student_id]
    seen = set()
    unique_tags = []
    for t in payload.tags:
        if t not in seen:
            seen.add(t)
            unique_tags.append(t)
    student.tags = unique_tags
    students[student_id] = student
    return student


@router.get("/{student_id}/appointment-hints", response_model=list[AppointmentHint])
def get_student_appointment_hints(student_id: int) -> list[AppointmentHint]:
    if student_id not in students:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Student not found")
    student = students[student_id]
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
    return hints
