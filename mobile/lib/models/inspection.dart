class InspectionTask {
  final int id;
  final int facilityId;
  final String facilityName;
  final String facilityCategory;
  final int templateId;
  final DateTime scheduledDate;
  final String status;
  final String priority;

  InspectionTask({
    required this.id,
    required this.facilityId,
    required this.facilityName,
    required this.facilityCategory,
    required this.templateId,
    required this.scheduledDate,
    required this.status,
    required this.priority,
  });

  factory InspectionTask.fromJson(Map<String, dynamic> json) {
    return InspectionTask(
      id: json['id'],
      facilityId: json['facility_id'],
      facilityName: json['facility_name'] ?? 'Facility #${json['facility_id']}',
      facilityCategory: json['facility_category'] ?? 'General',
      templateId: json['template_id'],
      scheduledDate: DateTime.parse(json['scheduled_date']),
      status: json['status'],
      priority: json['priority'] ?? 'NORMAL',
    );
  }
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
      questionText: json['question_text'],
      questionType: json['question_type'] ?? 'pass_fail',
      isRequired: json['is_required'] ?? true,
    );
  }
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
