enum MediaStatus {
  pending,
  compressing,
  completed,
  skipped,
  failed,
}

/// Represents a media candidate queued or processed for compression.
class MediaItem {
  final String path;
  final String fileName;
  final String codec;
  final String resolution;
  final int originalBytes;
  final int estimatedBytes;
  int finalBytes;
  double progress;
  MediaStatus status;
  String? error;

  MediaItem({
    required this.path,
    required this.fileName,
    required this.codec,
    required this.resolution,
    required this.originalBytes,
    required this.estimatedBytes,
    this.finalBytes = 0,
    this.progress = 0.0,
    this.status = MediaStatus.pending,
    this.error,
  });

  double get savingsRatio {
    if (originalBytes <= 0) return 0.0;
    final target = (status == MediaStatus.completed && finalBytes > 0)
        ? finalBytes
        : estimatedBytes;
    final saved = originalBytes - target;
    return (saved > 0) ? (saved / originalBytes) : 0.0;
  }

  static String formatBytes(int bytes) {
    if (bytes <= 0) return '0 B';
    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    int idx = 0;
    double val = bytes.toDouble();
    while (val >= 1024.0 && idx < units.length - 1) {
      val /= 1024.0;
      idx++;
    }
    return '${val.toStringAsFixed(1)} ${units[idx]}';
  }
}
