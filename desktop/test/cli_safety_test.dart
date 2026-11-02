import 'package:flutter_test/flutter_test.dart';
import 'package:desktop/services/mediacrush_cli.dart';

void main() {
  group('MediaCrushCli Safety & Probing', () {
    final cli = MediaCrushCli();

    test('videoExtensions contains required media containers', () {
      expect(MediaCrushCli.videoExtensions, contains('.mkv'));
      expect(MediaCrushCli.videoExtensions, contains('.mp4'));
      expect(MediaCrushCli.videoExtensions, contains('.webm'));
    });

    test('detectHardware returns fallback or hardware engine safely', () async {
      // Must complete without throwing and without spawning self
      final engine = await cli.detectHardware();
      expect(engine.name, isNotEmpty);
      expect(engine.vendor, isNotEmpty);
      expect(engine.codec, isNotEmpty);
    });

    test('scanDirectory returns empty list for invalid path', () async {
      final items = await cli.scanDirectory('C:/non_existent_folder_path_12345');
      expect(items, isEmpty);
    });
  });
}
