import 'dart:async';
import 'package:flutter/foundation.dart';
import '../models/compression_job.dart';
import '../models/hardware_engine.dart';
import '../models/media_item.dart';
import '../models/update_info.dart';
import '../services/mediacrush_cli.dart';
import '../services/update_service.dart';

/// Central state manager for MediaCrush Desktop UI.
class AppState extends ChangeNotifier {
  final MediaCrushCli _cli = MediaCrushCli();
  final UpdateService _updateService = UpdateService();

  HardwareEngine _hardware = HardwareEngine.fallback();
  UpdateInfo? _availableUpdate;
  List<MediaItem> _items = [];
  String? _selectedFolder;
  String _preset = 'anime';
  bool _isScanning = false;
  bool _isCompressing = false;
  CompressionJob? _job;

  HardwareEngine get hardware => _hardware;
  UpdateInfo? get availableUpdate => _availableUpdate;
  UpdateService get updateService => _updateService;
  List<MediaItem> get items => _items;
  String? get selectedFolder => _selectedFolder;
  String get preset => _preset;
  bool get isScanning => _isScanning;
  bool get isCompressing => _isCompressing;
  CompressionJob? get job => _job;

  int get totalCandidates => _items.length;
  int get totalOriginalBytes => _items.fold(0, (acc, item) => acc + item.originalBytes);
  int get totalEstimatedBytes => _items.fold(0, (acc, item) => acc + item.estimatedBytes);
  int get totalSavedBytes => (totalOriginalBytes - totalEstimatedBytes).clamp(0, totalOriginalBytes);
  double get savingsPercentage => totalOriginalBytes > 0 ? (totalSavedBytes / totalOriginalBytes) * 100.0 : 0.0;

  Future<void> initialize() async {
    _hardware = await _cli.detectHardware();
    notifyListeners();
    // Non-blocking update check
    _checkForUpdatesSilently();
  }

  Future<void> _checkForUpdatesSilently() async {
    final info = await _updateService.checkForUpdates();
    if (info.isAvailable) {
      _availableUpdate = info;
      notifyListeners();
    }
  }

  void setPreset(String newPreset) {
    _preset = newPreset;
    notifyListeners();
  }

  Future<void> scanFolder(String path) async {
    _selectedFolder = path;
    _isScanning = true;
    _items.clear();
    notifyListeners();

    _items = await _cli.scanDirectory(path);
    _isScanning = false;
    notifyListeners();
  }

  void startCompression() {
    if (_items.isEmpty || _isCompressing) return;
    _isCompressing = true;
    _job = CompressionJob(
      totalFiles: _items.length,
      originalTotalBytes: totalOriginalBytes,
      isRunning: true,
      currentFps: _hardware.typicalFps.toDouble(),
    );
    notifyListeners();
    _simulateStep();
  }

  void _simulateStep() {
    if (!_isCompressing || _items.isEmpty) return;
    Timer.periodic(const Duration(milliseconds: 300), (timer) {
      if (!_isCompressing || _job == null) {
        timer.cancel();
        return;
      }
      final pendingIndex = _items.indexWhere((it) => it.status == MediaStatus.pending || it.status == MediaStatus.compressing);
      if (pendingIndex == -1) {
        _isCompressing = false;
        _job?.isRunning = false;
        timer.cancel();
        notifyListeners();
        return;
      }
      final item = _items[pendingIndex];
      item.status = MediaStatus.compressing;
      item.progress += 0.25;
      if (item.progress >= 1.0) {
        item.progress = 1.0;
        item.status = MediaStatus.completed;
        item.finalBytes = item.estimatedBytes;
        _job!.completedFiles++;
      }
      _job!.overallProgress = _job!.completedFiles / _items.length;
      notifyListeners();
    });
  }

  void pauseCompression() {
    _isCompressing = false;
    _job?.isRunning = false;
    _cli.cancelActiveJob();
    notifyListeners();
  }
}
