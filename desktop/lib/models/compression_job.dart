/// Overall state and aggregated telemetry for a compression session.
class CompressionJob {
  final int totalFiles;
  int completedFiles;
  int currentFileIndex;
  double overallProgress;
  int originalTotalBytes;
  int finalTotalBytes;
  double currentFps;
  double currentSpeedMultiplier;
  String currentFileName;
  bool isPaused;
  bool isRunning;

  CompressionJob({
    required this.totalFiles,
    this.completedFiles = 0,
    this.currentFileIndex = 0,
    this.overallProgress = 0.0,
    this.originalTotalBytes = 0,
    this.finalTotalBytes = 0,
    this.currentFps = 0.0,
    this.currentSpeedMultiplier = 1.0,
    this.currentFileName = '',
    this.isPaused = false,
    this.isRunning = false,
  });

  int get totalSavedBytes {
    final diff = originalTotalBytes - finalTotalBytes;
    return diff > 0 ? diff : 0;
  }

  double get overallSavingsPercentage {
    if (originalTotalBytes <= 0) return 0.0;
    return (totalSavedBytes / originalTotalBytes) * 100.0;
  }
}
