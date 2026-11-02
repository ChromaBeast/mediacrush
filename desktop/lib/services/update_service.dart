import 'dart:convert';
import 'dart:io';
import 'package:path/path.dart' as p;
import '../models/update_info.dart';

/// Checks GitHub Releases and handles downloading/installing updates across desktop platforms.
class UpdateService {
  static const String repoOwner = 'ChromaBeast';
  static const String repoName = 'mediacrush';
  static const String currentVersion = '1.0.2';

  /// Queries GitHub Releases API for the latest published release.
  Future<UpdateInfo> checkForUpdates() async {
    try {
      final client = HttpClient();
      client.connectionTimeout = const Duration(seconds: 6);
      final uri = Uri.parse('https://api.github.com/repos/$repoOwner/$repoName/releases/latest');
      final request = await client.getUrl(uri);
      request.headers.set('User-Agent', 'MediaCrush-Desktop');
      request.headers.set('Accept', 'application/vnd.github.v3+json');

      final response = await request.close();
      if (response.statusCode != 200) {
        return UpdateInfo.none(currentVersion);
      }

      final body = await response.transform(utf8.decoder).join();
      final data = jsonDecode(body) as Map<String, dynamic>;

      final rawTag = (data['tag_name'] as String? ?? '').replaceAll('v', '').trim();
      final bodyText = data['body'] as String? ?? 'No release notes provided.';
      final assets = (data['assets'] as List<dynamic>?) ?? [];

      if (isVersionNewer(rawTag, currentVersion)) {
        final (assetName, downloadUrl) = resolvePlatformAsset(assets);
        return UpdateInfo(
          latestVersion: rawTag,
          currentVersion: currentVersion,
          releaseNotes: bodyText,
          downloadUrl: downloadUrl,
          assetName: assetName,
          isAvailable: true,
        );
      }
    } catch (_) {}

    return UpdateInfo.none(currentVersion);
  }

  /// Identifies the correct asset binary for the current operating system.
  (String?, String?) resolvePlatformAsset(List<dynamic> assets) {
    for (final a in assets) {
      if (a is! Map<String, dynamic>) continue;
      final name = (a['name'] as String? ?? '').toLowerCase();
      final url = a['browser_download_url'] as String?;

      if (Platform.isWindows && (name.endsWith('.exe') && name.contains('setup'))) {
        return (a['name'] as String?, url);
      } else if (Platform.isMacOS && name.endsWith('.dmg')) {
        return (a['name'] as String?, url);
      } else if (Platform.isLinux && (name.endsWith('.deb') || name.endsWith('.tar.gz'))) {
        return (a['name'] as String?, url);
      }
    }
    return (null, null);
  }

  /// Simple SemVer comparison: returns true if latest > current.
  bool isVersionNewer(String latest, String current) {
    if (latest.isEmpty) return false;
    final lParts = latest.split('.').map((e) => int.tryParse(e) ?? 0).toList();
    final cParts = current.split('.').map((e) => int.tryParse(e) ?? 0).toList();

    for (var i = 0; i < 3; i++) {
      final l = i < lParts.length ? lParts[i] : 0;
      final c = i < cParts.length ? cParts[i] : 0;
      if (l > c) return true;
      if (l < c) return false;
    }
    return false;
  }

  /// Downloads the update binary and executes it.
  Future<void> downloadAndApply(UpdateInfo info, void Function(double progress) onProgress) async {
    if (info.downloadUrl == null) return;

    final client = HttpClient();
    final request = await client.getUrl(Uri.parse(info.downloadUrl!));
    request.headers.set('User-Agent', 'MediaCrush-Desktop');
    final response = await request.close();

    final totalBytes = response.contentLength;
    var received = 0;

    final tempDir = Directory.systemTemp;
    final fileName = info.assetName ?? 'MediaCrushUpdate${Platform.isWindows ? ".exe" : ""}';
    final targetFile = File(p.join(tempDir.path, fileName));
    final sink = targetFile.openWrite();

    await for (final chunk in response) {
      sink.add(chunk);
      received += chunk.length;
      if (totalBytes > 0) {
        onProgress(received / totalBytes);
      }
    }
    await sink.flush();
    await sink.close();

    // Trigger installation on host OS
    if (Platform.isWindows) {
      await Process.start(targetFile.path, ['/SILENT'], mode: ProcessStartMode.detached);
      exit(0);
    } else if (Platform.isMacOS) {
      await Process.start('open', [targetFile.path]);
    } else if (Platform.isLinux) {
      await Process.start('xdg-open', [tempDir.path]);
    }
  }
}
