import 'package:flutter/material.dart';
import '../../models/update_info.dart';
import '../../services/update_service.dart';
import '../../theme/app_colors.dart';
import '../../theme/app_typography.dart';

/// Modal dialog for reviewing and applying an application update.
class UpdateDialog extends StatefulWidget {
  final UpdateInfo info;
  final UpdateService service;

  const UpdateDialog({
    super.key,
    required this.info,
    required this.service,
  });

  static Future<void> show(BuildContext context, UpdateInfo info, UpdateService service) {
    return showDialog(
      context: context,
      barrierDismissible: true,
      builder: (_) => UpdateDialog(info: info, service: service),
    );
  }

  @override
  State<UpdateDialog> createState() => _UpdateDialogState();
}

class _UpdateDialogState extends State<UpdateDialog> {
  bool _isDownloading = false;
  double _progress = 0.0;
  String? _error;

  Future<void> _startUpdate() async {
    setState(() {
      _isDownloading = true;
      _error = null;
    });

    try {
      await widget.service.downloadAndApply(widget.info, (p) {
        if (mounted) setState(() => _progress = p);
      });
    } catch (e) {
      if (mounted) {
        setState(() {
          _isDownloading = false;
          _error = 'Update failed: $e';
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Dialog(
      backgroundColor: AppColors.surfaceElevated,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12.0),
        side: BorderSide(color: AppColors.border),
      ),
      child: Container(
        width: 480,
        padding: const EdgeInsets.all(24.0),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.system_update_alt_rounded, color: AppColors.accent, size: 24),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    'MediaCrush Update Available (v${widget.info.latestVersion})',
                    style: AppTypography.title.copyWith(fontSize: 16),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Text(
              'A newer release is ready. Current version is v${widget.info.currentVersion}.',
              style: AppTypography.bodySecondary,
            ),
            const SizedBox(height: 14),
            Container(
              height: 120,
              width: double.infinity,
              padding: const EdgeInsets.all(12.0),
              decoration: BoxDecoration(
                color: AppColors.surface,
                borderRadius: BorderRadius.circular(8.0),
                border: Border.all(color: AppColors.border.withValues(alpha: 0.6)),
              ),
              child: SingleChildScrollView(
                child: Text(
                  widget.info.releaseNotes.isNotEmpty ? widget.info.releaseNotes : 'Performance improvements and bug fixes.',
                  style: AppTypography.monoCell,
                ),
              ),
            ),
            if (_error != null) ...[
              const SizedBox(height: 10),
              Text(_error!, style: AppTypography.bodySecondary.copyWith(color: AppColors.error)),
            ],
            if (_isDownloading) ...[
              const SizedBox(height: 16),
              LinearProgressIndicator(
                value: _progress > 0 ? _progress : null,
                backgroundColor: AppColors.surface,
                valueColor: const AlwaysStoppedAnimation<Color>(AppColors.accent),
              ),
              const SizedBox(height: 8),
              Text(
                'Downloading and preparing update (${(_progress * 100).toStringAsFixed(0)}%)...',
                style: AppTypography.label,
              ),
            ],
            const SizedBox(height: 20),
            Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                TextButton(
                  onPressed: _isDownloading ? null : () => Navigator.of(context).pop(),
                  child: Text('Later', style: AppTypography.bodySecondary),
                ),
                const SizedBox(width: 12),
                ElevatedButton.icon(
                  onPressed: _isDownloading ? null : _startUpdate,
                  icon: const Icon(Icons.download_rounded, size: 16),
                  label: Text(_isDownloading ? 'Updating...' : 'Update Now'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.accent,
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
