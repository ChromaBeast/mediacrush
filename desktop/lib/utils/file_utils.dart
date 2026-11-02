import 'dart:io';
import 'package:path/path.dart' as p;

/// Cross-platform file and folder launcher utility.
abstract final class FileUtils {
  /// Opens a folder in the operating system's native file explorer.
  static Future<void> openFolder(String folderPath) async {
    final dir = Directory(folderPath);
    if (!await dir.exists()) {
      await dir.create(recursive: true);
    }

    if (Platform.isWindows) {
      await Process.start('explorer.exe', [folderPath]);
    } else if (Platform.isMacOS) {
      await Process.start('open', [folderPath]);
    } else if (Platform.isLinux) {
      await Process.start('xdg-open', [folderPath]);
    }
  }

  /// Reveals a specific file in the native file manager, or opens its parent directory.
  static Future<void> revealFile(String filePath) async {
    final file = File(filePath);
    if (!await file.exists()) {
      await openFolder(p.dirname(filePath));
      return;
    }

    if (Platform.isWindows) {
      await Process.start('explorer.exe', ['/select,', p.normalize(filePath)]);
    } else if (Platform.isMacOS) {
      await Process.start('open', ['-R', filePath]);
    } else if (Platform.isLinux) {
      await Process.start('xdg-open', [p.dirname(filePath)]);
    }
  }

  /// Opens a file in its default system media player or viewer.
  static Future<void> openFile(String filePath) async {
    if (!await File(filePath).exists()) return;

    if (Platform.isWindows) {
      await Process.start('cmd.exe', ['/c', 'start', '', filePath]);
    } else if (Platform.isMacOS) {
      await Process.start('open', [filePath]);
    } else if (Platform.isLinux) {
      await Process.start('xdg-open', [filePath]);
    }
  }
}
