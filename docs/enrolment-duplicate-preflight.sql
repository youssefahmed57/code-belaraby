SELECT
  student_id,
  course_id,
  COUNT(*) AS duplicate_count
FROM enrolments
GROUP BY student_id, course_id
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC, student_id, course_id;
