import 'dart:async';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:path/path.dart' as p;
import '../models/compression_job.dart';
import '../models/hardware_engine.dart';
import '../models/media_item.dart';
import '../models/update_info.dart';
import '../services/mediacrush_cli.dart';
import '../services/transcode_service.dart';
import '../services/update_service.dart';
import '../utils/ffmpeg_locator.dart';
import '../utils/file_utils.dart';

/// Central state manager for MediaCrush Desktop UI.
class AppState extends ChangeNotifier {
  final MediaCrushCli _cli = MediaCrushCli();
  final UpdateService _updateService = UpdateService();
  final TranscodeService _transcoder = TranscodeService();

  HardwareEngine _hardware = HardwareEngine.fallback();
  UpdateInfo? _availableUpdate;
  List<MediaItem> _items = [];
  String? _selectedFolder;
  String? _outputFolder;
  String _preset = 'anime';
  bool _hasFfmpeg = true;
  bool _isScanning = false;
  bool _isCompressing = false;
  CompressionJob? _job;

  bool get hasFfmpeg => _hasFfmpeg;
  HardwareEngine get hardware => _hardware;
  UpdateInfo? get availableUpdate => _availableUpdate;
  UpdateService get updateService => _updateService;
  List<MediaItem> get items => _items;
  String? get selectedFolder => _selectedFolder;
  String? get outputFolder => _outputFolder;
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
    _hasFfmpeg = await FfmpegLocator.isFfmpegAvailable();
    _hardware = await _cli.detectHardware();
    notifyListeners();
    _checkForUpdatesSilently();
  }

  Future<void> _checkForUpdatesSilently() async {
    final info = await _updateService.checkForUpdates();
    if (info.isAvailable) {
      _availableUpdate = info;
      notifyListeners();
    }
  }

  Future<void> redetectHardware() async {
    _hardware = await _cli.detectHardware();
    notifyListeners();
  }

  void setHardware(HardwareEngine engine) {
    _hardware = engine;
    notifyListeners();
  }

  void setPreset(String newPreset) {
    _preset = newPreset;
    notifyListeners();
  }

  void setOutputFolder(String path) {
    _outputFolder = path;
    notifyListeners();
  }

  Future<void> openOutputFolder() async {
    if (_outputFolder != null) {
      await FileUtils.openFolder(_outputFolder!);
    } else if (_selectedFolder != null) {
      await FileUtils.openFolder(_selectedFolder!);
    }
  }

  Future<void> scanFolder(String path) async {
    _selectedFolder = path;
    _outputFolder ??= p.join(path, 'crushed');
    _isScanning = true;
    _items.clear();
    notifyListeners();

    _items = await _cli.scanDirectory(path);
    _isScanning = false;
    notifyListeners();
  }

  void addFiles(List<String> paths) {
    if (paths.isEmpty) return;
    _outputFolder ??= p.join(p.dirname(paths.first), 'crushed');
    for (final path in paths) {
      final f = File(path);
      if (f.existsSync() && !_items.any((it) => it.path == path)) {
        final size = f.lengthSync();
        _items.add(MediaItem(
          path: path,
          fileName: p.basename(path),
          codec: 'H.264',
          resolution: '1080p',
          originalBytes: size,
          estimatedBytes: (size * 0.45).round(),
        ));
      }
    }
    notifyListeners();
  }

  void clearItems() {
    if (_isCompressing) return;
    _items.clear();
    _selectedFolder = null;
    notifyListeners();
  }

  Future<void> startCompression() async {
    if (_items.isEmpty || _isCompressing) return;
    _isCompressing = true;
    _job = CompressionJob(
      totalFiles: _items.length,
      originalTotalBytes: totalOriginalBytes,
      isRunning: true,
      currentFps: _hardware.typicalFps.toDouble(),
    );
    notifyListeners();

    final destFolder = _outputFolder ?? p.join(_selectedFolder ?? Directory.current.path, 'crushed');
    await Directory(destFolder).create(recursive: true);

    for (var i = 0; i < _items.length; i++) {
      if (!_isCompressing) break;
      final item = _items[i];
      if (item.status == MediaStatus.completed) continue;

      item.status = MediaStatus.compressing;
      item.progress = 0.0;
      final targetName = '${p.basenameWithoutExtension(item.fileName)}.crushed.mp4';
      item.outputPath = p.join(destFolder, targetName);
      notifyListeners();

      final success = await _transcoder.transcode(
        inputPath: item.path,
        outputPath: item.outputPath!,
        engine: _hardware,
        preset: _preset,
        onProgress: (pct) {
          item.progress = pct;
          notifyListeners();
        },
      );

      if (success) {
        item.status = MediaStatus.completed;
        item.progress = 1.0;
        final outF = File(item.outputPath!);
        if (await outF.exists()) {
          item.finalBytes = await outF.length();
        }
        _job!.completedFiles++;
      } else {
        item.status = MediaStatus.failed;
      }
      _job!.overallProgress = _job!.completedFiles / _items.length;
      notifyListeners();
    }

    _isCompressing = false;
    _job?.isRunning = false;
    notifyListeners();
  }

  void pauseCompression() {
    _isCompressing = false;
    _job?.isRunning = false;
    _transcoder.cancel();
    notifyListeners();
  }
}
