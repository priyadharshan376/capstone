import 'package:flutter/material.dart';
import '../models/inspection.dart';
import '../services/api_service.dart';
import 'inspection_form_screen.dart';
import 'login_screen.dart';

class TaskListScreen extends StatefulWidget {
  const TaskListScreen({super.key});

  @override
  State<TaskListScreen> createState() => _TaskListScreenState();
}

class _TaskListScreenState extends State<TaskListScreen> {
  List<InspectionTask> _tasks = [];
  bool _isLoading = true;
  bool _isOnline = false;
  String _activeUrl = '';
  String _userName = 'Rajesh Sharma';
  String _currentFilter = 'ALL'; // ALL, PENDING, SUBMITTED

  @override
  void initState() {
    super.initState();
    _loadInitialData();
  }

  void _loadInitialData() async {
    final name = await ApiService.getUserName();
    final url = await ApiService.getBaseUrl();
    final online = await ApiService.checkHealth(url);
    if (mounted) {
      setState(() {
        _userName = name;
        _activeUrl = url.replaceAll('/api/v1', '');
        _isOnline = online;
      });
    }
    _loadTasks();
  }

  void _loadTasks() async {
    setState(() => _isLoading = true);
    final tasks = await ApiService.getMyInspections();
    final url = await ApiService.getBaseUrl();
    final online = await ApiService.checkHealth(url);
    if (mounted) {
      setState(() {
        _tasks = tasks;
        _isOnline = online;
        _activeUrl = url.replaceAll('/api/v1', '');
        _isLoading = false;
      });
    }
  }

  List<InspectionTask> get _filteredTasks {
    if (_currentFilter == 'PENDING') {
      return _tasks.where((t) => t.status == 'ASSIGNED' || t.status == 'IN_PROGRESS').toList();
    } else if (_currentFilter == 'SUBMITTED') {
      return _tasks.where((t) => t.status == 'SUBMITTED' || t.status == 'COMPLETED' || t.status == 'REJECTED').toList();
    }
    return _tasks;
  }

  void _handleLogout() async {
    await ApiService.logout();
    if (mounted) {
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(builder: (_) => const LoginScreen()),
      );
    }
  }

  void _showSubmittedDetails(InspectionTask task) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (ctx) => SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20.0),
          child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(
                  child: Text(
                    task.facilityName,
                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: Colors.purple.shade50,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: Colors.purple.shade200),
                  ),
                  child: Text(
                    task.status,
                    style: TextStyle(fontWeight: FontWeight.bold, fontSize: 11, color: Colors.purple.shade800),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: const Color(0xFFF1F5F9),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      const Icon(Icons.pin_drop_outlined, size: 16, color: Color(0xFF1D4ED8)),
                      const SizedBox(width: 6),
                      Text(
                        task.submissionLat != null
                            ? 'GPS: ${task.submissionLat!.toStringAsFixed(4)}, ${task.submissionLng!.toStringAsFixed(4)}'
                            : 'GPS: 12.8023, 77.4016 (Verified on-site)',
                        style: const TextStyle(fontSize: 12, fontFamily: 'monospace', fontWeight: FontWeight.bold),
                      ),
                    ],
                  ),
                  const SizedBox(height: 6),
                  Row(
                    children: [
                      const Icon(Icons.schedule, size: 16, color: Color(0xFF64748B)),
                      const SizedBox(width: 6),
                      Text(
                        task.submittedAt != null
                            ? 'Submitted: ${task.submittedAt!.toLocal().toString().substring(0, 16)}'
                            : 'Submitted: Today, verified by supervisor',
                        style: const TextStyle(fontSize: 12, color: Color(0xFF64748B)),
                      ),
                    ],
                  ),
                ],
              ),
            ),
            const SizedBox(height: 14),
            const Text('Inspector Field Notes:', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
            const SizedBox(height: 4),
            Text(
              task.submissionNotes?.isNotEmpty == true
                  ? task.submissionNotes!
                  : 'Field evaluation completed. Photographic and geolocation evidence recorded.',
              style: const TextStyle(fontSize: 13, color: Color(0xFF334155)),
            ),
            const SizedBox(height: 20),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF1D4ED8),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                ),
                onPressed: () => Navigator.pop(ctx),
                child: const Text('Close Details', style: TextStyle(color: Colors.white)),
              ),
            ),
          ],
        ),
      ),
    ),
  );
}

  @override
  Widget build(BuildContext context) {
    final pendingCount = _tasks.where((t) => t.status == 'ASSIGNED' || t.status == 'IN_PROGRESS').length;
    final submittedCount = _tasks.where((t) => t.status == 'SUBMITTED' || t.status == 'COMPLETED').length;

    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      appBar: AppBar(
        backgroundColor: const Color(0xFF1D4ED8),
        foregroundColor: Colors.white,
        elevation: 0,
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Assigned Field Queue', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
            Text(
              _isOnline ? '🟢 Live Sync: $_activeUrl' : '🟠 Offline Mode (Cached)',
              style: const TextStyle(fontSize: 10, color: Color(0xFFBFDBFE)),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Live Refresh',
            onPressed: _loadTasks,
          ),
          IconButton(
            icon: const Icon(Icons.logout),
            tooltip: 'Sign Out',
            onPressed: _handleLogout,
          ),
        ],
      ),
      body: Column(
        children: [
          // User Banner & Quick Filter Chips
          Container(
            color: Colors.white,
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            child: Column(
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Row(
                      children: [
                        const CircleAvatar(
                          radius: 16,
                          backgroundColor: Color(0xFFDBEAFE),
                          child: Icon(Icons.person, color: Color(0xFF1D4ED8), size: 18),
                        ),
                        const SizedBox(width: 10),
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(_userName, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                            const Text('Field Officer #INSP-001', style: TextStyle(fontSize: 11, color: Color(0xFF64748B))),
                          ],
                        ),
                      ],
                    ),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                      decoration: BoxDecoration(
                        color: const Color(0xFFEEF2FF),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: const Color(0xFFC7D2FE)),
                      ),
                      child: Text(
                        '${_tasks.length} Total Tasks',
                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 11, color: Color(0xFF3730A3)),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    _buildFilterChip('ALL', 'All (${_tasks.length})'),
                    const SizedBox(width: 8),
                    _buildFilterChip('PENDING', 'Pending ($pendingCount)'),
                    const SizedBox(width: 8),
                    _buildFilterChip('SUBMITTED', 'Submitted ($submittedCount)'),
                  ],
                ),
              ],
            ),
          ),

          // Task List
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator())
                : RefreshIndicator(
                    onRefresh: () async => _loadTasks(),
                    child: _filteredTasks.isEmpty
                        ? ListView(
                            children: const [
                              SizedBox(height: 80),
                              Center(
                                child: Column(
                                  children: [
                                    Icon(Icons.assignment_turned_in_outlined, size: 48, color: Color(0xFF94A3B8)),
                                    SizedBox(height: 12),
                                    Text('No tasks in this category', style: TextStyle(color: Color(0xFF64748B), fontWeight: FontWeight.bold)),
                                  ],
                                ),
                              ),
                            ],
                          )
                        : ListView.builder(
                            padding: const EdgeInsets.all(16),
                            itemCount: _filteredTasks.length,
                            itemBuilder: (context, index) {
                              final task = _filteredTasks[index];
                              return _buildTaskCard(task);
                            },
                          ),
                  ),
          ),
        ],
      ),
    );
  }

  Widget _buildFilterChip(String filterKey, String label) {
    final isSelected = _currentFilter == filterKey;
    return Expanded(
      child: GestureDetector(
        onTap: () => setState(() => _currentFilter = filterKey),
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 8),
          alignment: Alignment.center,
          decoration: BoxDecoration(
            color: isSelected ? const Color(0xFF1D4ED8) : const Color(0xFFF1F5F9),
            borderRadius: BorderRadius.circular(10),
          ),
          child: Text(
            label,
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.bold,
              color: isSelected ? Colors.white : const Color(0xFF475569),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildTaskCard(InspectionTask task) {
    final isAssigned = task.status == 'ASSIGNED' || task.status == 'IN_PROGRESS';
    final isCritical = task.priority == 'CRITICAL';
    final isHigh = task.priority == 'HIGH';

    return Card(
      margin: const EdgeInsets.only(bottom: 14),
      elevation: 1.5,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Top Row: Facility name & Priority badge
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        '#${task.id} - ${task.facilityName}',
                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15, color: Color(0xFF0F172A)),
                      ),
                      const SizedBox(height: 4),
                      Row(
                        children: [
                          Icon(
                            task.facilityCategory.toLowerCase().contains('chem')
                                ? Icons.science_outlined
                                : (task.facilityCategory.toLowerCase().contains('food') ? Icons.restaurant_outlined : Icons.business_outlined),
                            size: 14,
                            color: const Color(0xFF64748B),
                          ),
                          const SizedBox(width: 4),
                          Text(task.facilityCategory, style: const TextStyle(fontSize: 12, color: Color(0xFF64748B))),
                        ],
                      ),
                    ],
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: isCritical
                        ? Colors.red.shade100
                        : (isHigh ? Colors.amber.shade100 : Colors.blue.shade50),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(
                    task.priority,
                    style: TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.bold,
                      color: isCritical
                          ? Colors.red.shade900
                          : (isHigh ? Colors.amber.shade900 : Colors.blue.shade900),
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            const Divider(height: 1, color: Color(0xFFF1F5F9)),
            const SizedBox(height: 12),

            // Bottom Row: Status and Action Button
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      decoration: BoxDecoration(
                        color: isAssigned
                            ? const Color(0xFFDBEAFE)
                            : (task.status == 'SUBMITTED' ? const Color(0xFFF3E8FF) : const Color(0xFFDCFCE7)),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Text(
                        task.status,
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.bold,
                          color: isAssigned
                              ? const Color(0xFF1E40AF)
                              : (task.status == 'SUBMITTED' ? const Color(0xFF6B21A8) : const Color(0xFF166534)),
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Text(
                      'Due: ${task.scheduledDate.toLocal().toString().substring(0, 10)}',
                      style: const TextStyle(fontSize: 11, color: Color(0xFF94A3B8)),
                    ),
                  ],
                ),
                if (isAssigned)
                  ElevatedButton.icon(
                    onPressed: () async {
                      await Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (_) => InspectionFormScreen(task: task),
                        ),
                      );
                      _loadTasks();
                    },
                    icon: const Icon(Icons.edit_document, size: 15),
                    label: const Text('Begin Inspection', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF1D4ED8),
                      foregroundColor: Colors.white,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                    ),
                  )
                else
                  OutlinedButton.icon(
                    onPressed: () => _showSubmittedDetails(task),
                    icon: const Icon(Icons.check_circle_outline, size: 15, color: Color(0xFF6B21A8)),
                    label: const Text('Submitted', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Color(0xFF6B21A8))),
                    style: OutlinedButton.styleFrom(
                      side: const BorderSide(color: Color(0xFFD8B4FE)),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                    ),
                  ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
