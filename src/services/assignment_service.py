import json
import os
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

class AssignmentService:
    def __init__(self, data_path: str = "data"):
        self.data_path = data_path
        os.makedirs(data_path, exist_ok=True)
        self.assignments_file = os.path.join(data_path, "assignments.json")
        self.submissions_file = os.path.join(data_path, "assignment_submissions.json")
        self._ensure_files()

    def _ensure_files(self):
        if not os.path.exists(self.assignments_file):
            with open(self.assignments_file, 'w', encoding='utf-8') as f:
                json.dump([], f, indent=2, ensure_ascii=False)
        if not os.path.exists(self.submissions_file):
            with open(self.submissions_file, 'w', encoding='utf-8') as f:
                json.dump([], f, indent=2, ensure_ascii=False)

    def _load(self, path: str) -> Any:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _save(self, path: str, data: Any):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    # Assignments
    def create_assignment(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        assignments = self._load(self.assignments_file)
        new_item = {
            "id": str(uuid.uuid4()),
            "title": payload.get("title", ""),
            "description": payload.get("description", ""),
            "subject": payload.get("subject", "General"),
            "due_date": payload.get("due_date"),
            "creator_teacher_id": payload.get("creator_teacher_id") or "unknown_teacher",
            "target_type": payload.get("target_type", "all"),  # all | class | students
            "target_ids": payload.get("target_ids", []),
            "status": "active",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        assignments.append(new_item)
        self._save(self.assignments_file, assignments)
        return new_item

    def list_assignments(self, teacher_id: Optional[str] = None, class_id: Optional[str] = None) -> List[Dict[str, Any]]:
        assignments = self._load(self.assignments_file)
        result = [a for a in assignments if (teacher_id is None or a.get("creator_teacher_id") == teacher_id)]
        # class_id filtering placeholder (no class model yet)
        return result

    def get_assignment(self, assignment_id: str) -> Optional[Dict[str, Any]]:
        assignments = self._load(self.assignments_file)
        return next((a for a in assignments if a["id"] == assignment_id), None)

    def update_assignment_status(self, assignment_id: str, status: str) -> Optional[Dict[str, Any]]:
        assignments = self._load(self.assignments_file)
        found = None
        for a in assignments:
            if a["id"] == assignment_id:
                a["status"] = status
                a["updated_at"] = datetime.now().isoformat()
                found = a
                break
        if found:
            self._save(self.assignments_file, assignments)
        return found

    # Submissions
    def submit(self, assignment_id: str, student_id: str, content: str) -> Dict[str, Any]:
        submissions = self._load(self.submissions_file)
        # If resubmission, overwrite content
        existing = next((s for s in submissions if s["assignment_id"] == assignment_id and s["student_id"] == student_id), None)
        if existing:
            existing["content"] = content
            existing["submitted_at"] = datetime.now().isoformat()
            existing["status"] = "submitted"
            self._save(self.submissions_file, submissions)
            return existing
        new_sub = {
            "id": str(uuid.uuid4()),
            "assignment_id": assignment_id,
            "student_id": student_id,
            "content": content,
            "submitted_at": datetime.now().isoformat(),
            "grade": None,
            "feedback": None,
            "status": "submitted"
        }
        submissions.append(new_sub)
        self._save(self.submissions_file, submissions)
        return new_sub

    def list_submissions(self, assignment_id: str) -> List[Dict[str, Any]]:
        submissions = self._load(self.submissions_file)
        return [s for s in submissions if s.get("assignment_id") == assignment_id]

    def get_submission(self, assignment_id: str, student_id: str) -> Optional[Dict[str, Any]]:
        submissions = self._load(self.submissions_file)
        return next((s for s in submissions if s["assignment_id"] == assignment_id and s["student_id"] == student_id), None)

    def grade_submission(self, submission_id: str, grade: float, feedback: str) -> Optional[Dict[str, Any]]:
        submissions = self._load(self.submissions_file)
        target = None
        for s in submissions:
            if s["id"] == submission_id:
                s["grade"] = grade
                s["feedback"] = feedback
                s["graded_at"] = datetime.now().isoformat()
                target = s
                break
        if target:
            self._save(self.submissions_file, submissions)
        return target

    def list_assignments_for_student(self, student_id: str) -> List[Dict[str, Any]]:
        assignments = self._load(self.assignments_file)
        submissions = self._load(self.submissions_file)
        submitted_map = { (s["assignment_id"], s["student_id"]): s for s in submissions }
        # Basic targeting: all or explicit list of student ids
        result = []
        for a in assignments:
            if a.get("target_type") == "all" or (a.get("target_type") == "students" and student_id in a.get("target_ids", [])):
                sub = submitted_map.get((a["id"], student_id))
                a_view = { **a }
                if sub:
                    a_view["submission_status"] = sub.get("status")
                    a_view["submitted_at"] = sub.get("submitted_at")
                    a_view["grade"] = sub.get("grade")
                else:
                    a_view["submission_status"] = "pending"
                result.append(a_view)
        return result

assignment_service = AssignmentService()
