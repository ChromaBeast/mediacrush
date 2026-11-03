import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../state/app_state.dart';
import '../../theme/app_colors.dart';
import '../../theme/app_typography.dart';

/// Bottom action bar with status summary, output folder button, and execution control.
class FooterControlBar extends StatelessWidget {
  const FooterControlBar({super.key});

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();
    final job = state.job;

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 20.0, vertical: 12.0),
      decoration: BoxDecoration(
        color: AppColors.background,
        border: Border(top: BorderSide(color: AppColors.border)),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  _buildStatusText(state),
                  style: AppTypography.bodySecondary,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              const SizedBox(width: 12.0),
              if (state.outputFolder != null) ...[
                OutlinedButton.icon(
                  onPressed: () => state.openOutputFolder(),
                  icon: const Icon(Icons.folder_shared_outlined, size: 16),
                  label: const Text('Open Output Folder'),
                  style: OutlinedButton.styleFrom(
                    foregroundColor: AppColors.textPrimary,
                    side: BorderSide(color: AppColors.border),
                    padding: const EdgeInsets.symmetric(horizontal: 14.0, vertical: 10.0),
                    textStyle: AppTypography.bodySecondary,
                  ),
                ),
                const SizedBox(width: 10.0),
              ],
              if (state.isCompressing)
                FilledButton.tonal(
                  onPressed: () => state.pauseCompression(),
                  style: FilledButton.styleFrom(
                    padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 10.0),
                  ),
                  child: const Text('Stop'),
                )
              else
                FilledButton.icon(
                  onPressed: (state.items.isEmpty || !state.hasFfmpeg) ? null : () => state.startCompression(),
                  icon: const Icon(Icons.play_arrow_rounded, size: 18),
                  label: const Text('Start Compression'),
                  style: FilledButton.styleFrom(
                    backgroundColor: AppColors.accent,
                    foregroundColor: Colors.white,
                    disabledBackgroundColor: AppColors.surfaceElevated,
                    padding: const EdgeInsets.symmetric(horizontal: 18.0, vertical: 10.0),
                    textStyle: AppTypography.subtitle,
                  ),
                ),
            ],
          ),
          if (state.isCompressing && job != null) ...[
            const SizedBox(height: 10.0),
            ClipRRect(
              borderRadius: BorderRadius.circular(3.0),
              child: LinearProgressIndicator(
                value: job.overallProgress > 0 ? job.overallProgress : null,
                backgroundColor: AppColors.surfaceElevated,
                valueColor: const AlwaysStoppedAnimation<Color>(AppColors.accent),
                minHeight: 4.0,
              ),
            ),
          ],
        ],
      ),
    );
  }

  String _buildStatusText(AppState state) {
    if (!state.hasFfmpeg) {
      return 'Warning: FFmpeg binary not detected. Please ensure FFmpeg is available.';
    }
    if (state.isScanning) {
      return 'Scanning media files...';
    }
    if (state.isCompressing && state.job != null) {
      final job = state.job!;
      return 'Compressing: ${job.completedFiles} of ${job.totalFiles} files • Using ${state.hardware.name}';
    }
    if (state.items.isNotEmpty) {
      return '${state.items.length} files queued. Projected savings: ${state.savingsPercentage.toStringAsFixed(1)}%';
    }
    return 'Add files or a folder to start compressing';
  }
}
