import 'package:flutter_test/flutter_test.dart';
import 'package:desktop/models/hardware_engine.dart';
import 'package:desktop/models/media_item.dart';

MediaItem item({int original = 1000, int estimated = 450, int fin = 0, MediaStatus status = MediaStatus.pending}) =>
    MediaItem(
      path: '/a.mkv',
      fileName: 'a.mkv',
      codec: 'H.264',
      resolution: '1080p',
      originalBytes: original,
      estimatedBytes: estimated,
      finalBytes: fin,
      status: status,
    );

void main() {
  group('HardwareEngine.fromCliName', () {
    const table = {
      'hevc_nvenc': ['hevc_nvenc', 'NVIDIA', 'HEVC'],
      'nvenc': ['hevc_nvenc', 'NVIDIA', 'HEVC'],
      'av1_nvenc': ['av1_nvenc', 'NVIDIA', 'AV1'],
      'hevc_videotoolbox': ['hevc_videotoolbox', 'Apple', 'HEVC'],
      'videotoolbox': ['hevc_videotoolbox', 'Apple', 'HEVC'],
      'hevc_amf': ['hevc_amf', 'AMD', 'HEVC'],
      'amf': ['hevc_amf', 'AMD', 'HEVC'],
      'hevc_qsv': ['hevc_qsv', 'Intel', 'HEVC'],
      'qsv': ['hevc_qsv', 'Intel', 'HEVC'],
      'hevc_vaapi': ['hevc_vaapi', 'Linux/Mesa', 'HEVC'],
      'vaapi': ['hevc_vaapi', 'Linux/Mesa', 'HEVC'],
    };

    table.forEach((input, expected) {
      test('maps "$input"', () {
        final e = HardwareEngine.fromCliName(input);
        expect([e.name, e.vendor, e.codec], expected);
        expect(e.isHardware, isTrue);
        expect(e.typicalFps, greaterThan(0));
      });
    });

    test('is case-insensitive', () {
      expect(HardwareEngine.fromCliName('HEVC_NVENC').vendor, 'NVIDIA');
    });

    test('unknown and empty names fall back to CPU', () {
      for (final n in ['', 'libx264', 'garbage']) {
        final e = HardwareEngine.fromCliName(n);
        expect(e.name, 'libx265');
        expect(e.isHardware, isFalse);
        expect(e.vendor, 'CPU');
      }
    });

    test('fallback is software HEVC', () {
      final f = HardwareEngine.fallback();
      expect(f.codec, 'HEVC');
      expect(f.isHardware, isFalse);
    });
  });

  group('MediaItem.formatBytes', () {
    test('zero and negative', () {
      expect(MediaItem.formatBytes(0), '0 B');
      expect(MediaItem.formatBytes(-10), '0 B');
    });

    test('unit boundaries', () {
      expect(MediaItem.formatBytes(1), '1.0 B');
      expect(MediaItem.formatBytes(1023), '1023.0 B');
      expect(MediaItem.formatBytes(1536), '1.5 KB');
      expect(MediaItem.formatBytes(1024 * 1024 * 1024 * 1024), '1.0 TB');
    });

    test('caps at TB', () {
      expect(MediaItem.formatBytes(1024 * 1024 * 1024 * 1024 * 2048), endsWith('TB'));
    });
  });

  group('MediaItem.savingsRatio', () {
    test('uses estimate while pending', () {
      expect(item().savingsRatio, closeTo(0.55, 1e-9));
    });

    test('uses actual size once completed', () {
      expect(item(fin: 200, status: MediaStatus.completed).savingsRatio, closeTo(0.8, 1e-9));
    });

    test('falls back to estimate when completed with unknown final size', () {
      expect(item(fin: 0, status: MediaStatus.completed).savingsRatio, closeTo(0.55, 1e-9));
    });

    test('never negative if estimate exceeds original', () {
      expect(item(estimated: 2000).savingsRatio, 0.0);
    });

    test('zero for empty files', () {
      expect(item(original: 0, estimated: 0).savingsRatio, 0.0);
    });

    test('defaults', () {
      final i = item();
      expect(i.status, MediaStatus.pending);
      expect(i.progress, 0.0);
      expect(i.outputPath, isNull);
      expect(i.error, isNull);
    });
  });
}
