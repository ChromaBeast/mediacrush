import 'package:flutter_test/flutter_test.dart';
import 'package:desktop/models/compression_job.dart';

void main() {
  group('CompressionJob', () {
    test('defaults', () {
      final j = CompressionJob(totalFiles: 3);
      expect(j.completedFiles, 0);
      expect(j.overallProgress, 0.0);
      expect(j.isRunning, isFalse);
      expect(j.isPaused, isFalse);
      expect(j.currentSpeedMultiplier, 1.0);
      expect(j.totalSavedBytes, 0);
    });

    test('totalSavedBytes is the difference', () {
      final j = CompressionJob(totalFiles: 1, originalTotalBytes: 1000, finalTotalBytes: 400);
      expect(j.totalSavedBytes, 600);
      expect(j.overallSavingsPercentage, closeTo(60.0, 1e-9));
    });

    test('totalSavedBytes never negative when output grows', () {
      final j = CompressionJob(totalFiles: 1, originalTotalBytes: 100, finalTotalBytes: 500);
      expect(j.totalSavedBytes, 0);
      expect(j.overallSavingsPercentage, 0.0);
    });

    test('percentage is zero when nothing to compress', () {
      expect(CompressionJob(totalFiles: 0).overallSavingsPercentage, 0.0);
      expect(CompressionJob(totalFiles: 1, originalTotalBytes: -5).overallSavingsPercentage, 0.0);
    });

    test('fields are mutable for live progress', () {
      final j = CompressionJob(totalFiles: 2)
        ..completedFiles = 1
        ..overallProgress = 0.5
        ..isRunning = true;
      expect(j.completedFiles, 1);
      expect(j.overallProgress, 0.5);
      expect(j.isRunning, isTrue);
    });
  });
}
