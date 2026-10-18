class InspectionTask {
  final int id;
  final int facilityId;
  final String facilityName;
  final String facilityCategory;
  final int templateId;
  final DateTime scheduledDate;
  String status;
  final String priority;
  String? submissionNotes;
  double? submissionLat;
  double? submissionLng;
  DateTime? submittedAt;
  String? supervisorFeedback;

  InspectionTask({
    required this.id,
    required this.facilityId,
    required this.facilityName,
    required this.facilityCategory,
    required this.templateId,
    required this.scheduledDate,
    required this.status,
    required this.priority,
    this.submissionNotes,
    this.submissionLat,
    this.submissionLng,
    this.submittedAt,
    this.supervisorFeedback,
  });

  factory InspectionTask.fromJson(Map<String, dynamic> json) {
    return InspectionTask(
      id: json['id'],
      facilityId: json['facility_id'],
      facilityName: json['facility_name'] ?? 'Facility #${json['facility_id']}',
      facilityCategory: json['facility_category'] ?? 'General Industry',
      templateId: json['template_id'],
      scheduledDate: DateTime.parse(json['scheduled_date']),
      status: json['status'],
      priority: json['priority'] ?? 'NORMAL',
      submissionNotes: json['submission_notes'],
      submissionLat: (json['submission_lat'] as num?)?.toDouble(),
      submissionLng: (json['submission_lng'] as num?)?.toDouble(),
      submittedAt: json['submitted_at'] != null ? DateTime.tryParse(json['submitted_at']) : null,
      supervisorFeedback: json['supervisor_feedback'],
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'facility_id': facilityId,
    'facility_name': facilityName,
    'facility_category': facilityCategory,
    'template_id': templateId,
    'scheduled_date': scheduledDate.toIso8601String(),
    'status': status,
    'priority': priority,
    'submission_notes': submissionNotes,
    'submission_lat': submissionLat,
    'submission_lng': submissionLng,
    'submitted_at': submittedAt?.toIso8601String(),
    'supervisor_feedback': supervisorFeedback,
  };
}

class ChecklistQuestion {
  final int id;
  final String questionText;
  final String questionType;
  final bool isRequired;

  ChecklistQuestion({
    required this.id,
    required this.questionText,
    required this.questionType,
    required this.isRequired,
  });

  factory ChecklistQuestion.fromJson(Map<String, dynamic> json) {
    return ChecklistQuestion(
      id: json['id'],
      questionText: json['question_text'] ?? json['question'] ?? '',
      questionType: json['question_type'] ?? 'pass_fail',
      isRequired: json['is_required'] ?? true,
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'question_text': questionText,
    'question_type': questionType,
    'is_required': isRequired,
  };
}

class FindingSubmission {
  final int checklistItemId;
  String status; // PASS, FAIL, NA
  String notes;
  String? photoUrl;
  double? gpsLat;
  double? gpsLng;

  FindingSubmission({
    required this.checklistItemId,
    this.status = 'PASS',
    this.notes = '',
    this.photoUrl,
    this.gpsLat,
    this.gpsLng,
  });

  Map<String, dynamic> toJson() => {
    'checklist_item_id': checklistItemId,
    'status': status,
    'notes': notes,
    'photo_url': photoUrl,
    'gps_lat': gpsLat,
    'gps_lng': gpsLng,
  };
}
