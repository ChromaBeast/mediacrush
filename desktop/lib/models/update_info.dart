/// Metadata regarding an available application update.
class UpdateInfo {
  final String latestVersion;
  final String currentVersion;
  final String releaseNotes;
  final String? downloadUrl;
  final String? assetName;
  final bool isAvailable;

  const UpdateInfo({
    required this.latestVersion,
    required this.currentVersion,
    required this.releaseNotes,
    this.downloadUrl,
    this.assetName,
    required this.isAvailable,
  });

  factory UpdateInfo.none(String current) {
    return UpdateInfo(
      latestVersion: current,
      currentVersion: current,
      releaseNotes: '',
      isAvailable: false,
    );
  }
}
