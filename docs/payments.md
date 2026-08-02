# Manual Payments Documentation (InstaPay & Vodafone Cash)

## Overview
Code Journey Academy implements a secure manual payment workflow tailored for Egyptian students. The workflow prevents fake automated API claims while delivering a fast, transactional approval process.

## Payment Workflow Steps

1. **Course Selection**: Student selects a course and clicks "اشترك الآن".
2. **Order Generation**: API generates a unique payment reference (e.g. `PAY-20260801-A1B2C3`).
3. **External Transfer**: Student transfers payment to:
   - **InstaPay**: `01001340533`
   - **Vodafone Cash**: `01001340533`
4. **Receipt Submission**: Student uploads a screenshot image (JPG/PNG) or PDF proof, enters sender phone number and submitted amount. Status transitions to `Pending Review`.
5. **Admin Review Drawer**: Admin verifies transaction in the admin panel, previews receipt, and clicks **Approve**.
6. **Transactional Activation**: Approval transactionally:
   - Updates payment status to `Approved`.
   - Creates or activates student enrolment for 365 days.
   - Unlocks Lesson 1.
   - Logs an audit event.
   - Sends an in-platform notification.
7. **Pre-filled WhatsApp Message**: Student can optionally click WhatsApp button with pre-filled message:
   ```text
   السلام عليكم، أرغب في تأكيد اشتراكي.
   اسم الطالب: [اسم الطالب]
   الكورس: [اسم الكورس]
   مرجع طلب الدفع: [PAY-20260801-XXXXXX]
   وسيلة الدفع: [انستا باي / فودافون كاش]
   المبلغ: [180 ج.م]
   ```
