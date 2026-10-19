import 'package:flutter/material.dart';
import '../services/api_service.dart';
import 'task_list_screen.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _emailController = TextEditingController(text: 'rajesh@inspect.gov.in');
  final _passwordController = TextEditingController(text: 'Insp@123');
  bool _isLoading = false;
  String _activeServerUrl = 'Detecting...';
  bool _isServerOnline = false;

  @override
  void initState() {
    super.initState();
    _checkServerStatus();
  }

  void _checkServerStatus() async {
    final active = await ApiService.autoDiscoverWorkingUrl() ?? await ApiService.getBaseUrl();
    final online = await ApiService.checkHealth(active);
    if (mounted) {
      setState(() {
        _activeServerUrl = active.replaceAll('/api/v1', '');
        _isServerOnline = online;
      });
    }
  }

  void _handleLogin() async {
    setState(() => _isLoading = true);
    final result = await ApiService.login(
      _emailController.text.trim(),
      _passwordController.text.trim(),
    );
    setState(() => _isLoading = false);

    if (result['success'] == true && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(result['message']),
          backgroundColor: result['is_online'] ? Colors.green.shade700 : Colors.amber.shade800,
          duration: const Duration(seconds: 3),
        ),
      );
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(builder: (_) => const TaskListScreen()),
      );
    } else if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(result['message'] ?? 'Login failed. Please check credentials.'),
          backgroundColor: Colors.red.shade700,
        ),
      );
    }
  }

  void _showServerSettingsDialog() async {
    final currentUrl = await ApiService.getBaseUrl();
    final urlController = TextEditingController(text: currentUrl);
    bool testing = false;
    String testResult = '';

    if (!mounted) return;
    showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
          title: const Row(
            children: [
              Icon(Icons.hub_outlined, color: Color(0xFF1D4ED8)),
              SizedBox(width: 10),
              Text('Backend Connection', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            ],
          ),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Select connection mode or enter your laptop IP:',
                  style: TextStyle(fontSize: 12, color: Color(0xFF64748B)),
                ),
                const SizedBox(height: 12),
                Wrap(
                  spacing: 6,
                  runSpacing: 6,
                  children: [
                    _buildPresetChip('USB Cable', 'http://127.0.0.1:8000/api/v1', urlController, setDialogState),
                    _buildPresetChip('Wi-Fi Network', 'http://10.187.110.33:8000/api/v1', urlController, setDialogState),
                    _buildPresetChip('Emulator', 'http://10.0.2.2:8000/api/v1', urlController, setDialogState),
                  ],
                ),
                const SizedBox(height: 14),
                TextField(
                  controller: urlController,
                  style: const TextStyle(fontSize: 13, fontFamily: 'monospace'),
                  decoration: InputDecoration(
                    labelText: 'Server Base URL',
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                    prefixIcon: const Icon(Icons.link, size: 20),
                  ),
                ),
                const SizedBox(height: 10),
                if (testResult.isNotEmpty)
                  Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: testResult.startsWith('✅') ? Colors.green.shade50 : Colors.red.shade50,
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: testResult.startsWith('✅') ? Colors.green.shade200 : Colors.red.shade200),
                    ),
                    child: Text(testResult, style: TextStyle(fontSize: 11, color: testResult.startsWith('✅') ? Colors.green.shade900 : Colors.red.shade900)),
                  ),
                const SizedBox(height: 8),
                TextButton.icon(
                  onPressed: testing ? null : () async {
                    setDialogState(() {
                      testing = true;
                      testResult = 'Pinging server...';
                    });
                    final ok = await ApiService.checkHealth(urlController.text.trim());
                    setDialogState(() {
                      testing = false;
                      testResult = ok ? '✅ Server healthy & responding (200 OK)!' : '❌ Server unreachable. Verify server is running on port 8000.';
                    });
                  },
                  icon: testing
                      ? const SizedBox(width: 14, height: 14, child: CircularProgressIndicator(strokeWidth: 2))
                      : const Icon(Icons.network_check, size: 16),
                  label: const Text('Test Ping Now', style: TextStyle(fontSize: 12)),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: const Text('Cancel'),
            ),
            ElevatedButton(
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF1D4ED8),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
              ),
              onPressed: () async {
                await ApiService.setBaseUrl(urlController.text.trim());
                if (ctx.mounted) Navigator.pop(ctx);
                _checkServerStatus();
              },
              child: const Text('Save & Apply', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPresetChip(String label, String url, TextEditingController controller, StateSetter setDialogState) {
    final isSelected = controller.text.trim() == url;
    return ChoiceChip(
      label: Text(label, style: const TextStyle(fontSize: 11)),
      selected: isSelected,
      onSelected: (_) {
        setDialogState(() {
          controller.text = url;
        });
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        actions: [
          IconButton(
            icon: const Icon(Icons.settings_outlined, color: Color(0xFF64748B)),
            tooltip: 'Server Connection Settings',
            onPressed: _showServerSettingsDialog,
          ),
        ],
      ),
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 24.0),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                // Server Connection Status Pill
                InkWell(
                  onTap: _showServerSettingsDialog,
                  borderRadius: BorderRadius.circular(20),
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                    decoration: BoxDecoration(
                      color: _isServerOnline ? const Color(0xFFECFDF5) : const Color(0xFFFEF2F2),
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(color: _isServerOnline ? const Color(0xFFA7F3D0) : const Color(0xFFFECACA)),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Container(
                          width: 8,
                          height: 8,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            color: _isServerOnline ? const Color(0xFF10B981) : Colors.red,
                          ),
                        ),
                        const SizedBox(width: 8),
                        Text(
                          _isServerOnline ? 'Server: $_activeServerUrl' : 'Server Offline: Tap to configure',
                          style: TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.w600,
                            color: _isServerOnline ? const Color(0xFF065F46) : const Color(0xFF991B1B),
                          ),
                        ),
                        const SizedBox(width: 4),
                        const Icon(Icons.arrow_drop_down, size: 16, color: Color(0xFF64748B)),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 24),

                // Shield Logo
                Container(
                  width: 72,
                  height: 72,
                  decoration: BoxDecoration(
                    color: const Color(0xFF1D4ED8),
                    borderRadius: BorderRadius.circular(22),
                    boxShadow: const [
                      BoxShadow(
                        color: Color(0x4D1D4ED8),
                        blurRadius: 18,
                        offset: Offset(0, 8),
                      ),
                    ],
                  ),
                  child: const Icon(Icons.shield_outlined, color: Colors.white, size: 38),
                ),
                const SizedBox(height: 18),
                const Text(
                  'Smart Inspection',
                  style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Color(0xFF0F172A)),
                ),
                const Text(
                  'Field Inspector Mobile Portal',
                  style: TextStyle(fontSize: 13, color: Color(0xFF64748B)),
                ),
                const SizedBox(height: 32),

                // Inputs
                TextField(
                  controller: _emailController,
                  decoration: InputDecoration(
                    labelText: 'Official Inspector Email',
                    prefixIcon: const Icon(Icons.email_outlined),
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(14)),
                    filled: true,
                    fillColor: Colors.white,
                  ),
                ),
                const SizedBox(height: 14),
                TextField(
                  controller: _passwordController,
                  obscureText: true,
                  decoration: InputDecoration(
                    labelText: 'Password',
                    prefixIcon: const Icon(Icons.lock_outline),
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(14)),
                    filled: true,
                    fillColor: Colors.white,
                  ),
                ),
                const SizedBox(height: 24),

                // Sign In Button
                SizedBox(
                  width: double.infinity,
                  height: 52,
                  child: ElevatedButton(
                    onPressed: _isLoading ? null : _handleLogin,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF1D4ED8),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                      elevation: 2,
                    ),
                    child: _isLoading
                        ? const CircularProgressIndicator(color: Colors.white)
                        : const Text(
                            'Sign In as Field Inspector',
                            style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: Colors.white),
                          ),
                  ),
                ),
                const SizedBox(height: 16),
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const Text('Default user: ', style: TextStyle(fontSize: 11, color: Color(0xFF94A3B8))),
                    GestureDetector(
                      onTap: () {
                        _emailController.text = 'rajesh@inspect.gov.in';
                        _passwordController.text = 'Insp@123';
                      },
                      child: const Text('rajesh@inspect.gov.in', style: TextStyle(fontSize: 11, color: Color(0xFF1D4ED8), fontWeight: FontWeight.bold)),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
