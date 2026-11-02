import 'package:flutter_test/flutter_test.dart';
import 'package:desktop/models/hardware_engine.dart';
import 'package:desktop/models/media_item.dart';

void main() {
  group('HardwareEngine', () {
    test('parses hevc_nvenc correctly', () {
      final engine = HardwareEngine.fromCliName('hevc_nvenc');
      expect(engine.name, equals('hevc_nvenc'));
      expect(engine.vendor, equals('NVIDIA'));
      expect(engine.typicalFps, equals(240));
    });

    test('falls back safely for unknown encoder', () {
      final engine = HardwareEngine.fromCliName('unknown_test');
      expect(engine.name, equals('libx265'));
      expect(engine.isHardware, isFalse);
    });
  });

  group('MediaItem', () {
    test('formats bytes correctly', () {
      expect(MediaItem.formatBytes(1024), equals('1.0 KB'));
      expect(MediaItem.formatBytes(1048576), equals('1.0 MB'));
      expect(MediaItem.formatBytes(1073741824), equals('1.0 GB'));
    });

    test('calculates savings ratio accurately', () {
      final item = MediaItem(
        path: '/dummy.mkv',
        fileName: 'dummy.mkv',
        codec: 'H.264',
        resolution: '1080p',
        originalBytes: 1000,
        estimatedBytes: 450,
      );
      expect(item.savingsRatio, closeTo(0.55, 0.01));
    });
  });
}
