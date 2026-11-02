import 'package:flutter/material.dart';
import '../../models/media_item.dart';
import '../../theme/app_colors.dart';
import '../../theme/app_typography.dart';
import '../../utils/file_utils.dart';
import '../common/badge_pill.dart';

/// Single item row in the media queue table.
class MediaRowItem extends StatelessWidget {
  final MediaItem item;
  final bool isEven;

  const MediaRowItem({
    super.key,
    required this.item,
    required this.isEven,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 8.0),
      color: isEven ? AppColors.surface : AppColors.surfaceElevated.withValues(alpha: 0.4),
      child: Row(
        children: [
          Expanded(
            flex: 4,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  item.fileName,
                  style: AppTypography.body,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                if (item.outputPath != null && item.status == MediaStatus.completed)
                  Text(
                    item.outputPath!,
                    style: AppTypography.label.copyWith(fontSize: 10, color: AppColors.textMuted),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
              ],
            ),
          ),
          const SizedBox(width: 8.0),
          SizedBox(
            width: 70,
            child: Align(
              alignment: Alignment.centerLeft,
              child: BadgePill.codec(item.codec),
            ),
          ),
          SizedBox(
            width: 60,
            child: Text(item.resolution, style: AppTypography.bodySecondary),
          ),
          SizedBox(
            width: 90,
            child: Text(MediaItem.formatBytes(item.originalBytes), style: AppTypography.bodySecondary),
          ),
          SizedBox(
            width: 90,
            child: Text(
              MediaItem.formatBytes(item.status == MediaStatus.completed ? item.finalBytes : item.estimatedBytes),
              style: AppTypography.bodySecondary.copyWith(
                color: item.status == MediaStatus.completed ? AppColors.success : AppColors.accent,
              ),
            ),
          ),
          SizedBox(
            width: 65,
            child: Text(
              '-${(item.savingsRatio * 100).toStringAsFixed(0)}%',
              style: AppTypography.bodySecondary.copyWith(color: AppColors.success),
            ),
          ),
          SizedBox(
            width: 130,
            child: _buildStatusWidget(),
          ),
        ],
      ),
    );
  }

  Widget _buildStatusWidget() {
    switch (item.status) {
      case MediaStatus.pending:
        return BadgePill.status(text: 'Queued', color: AppColors.textMuted);
      case MediaStatus.compressing:
        return Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            LinearProgressIndicator(
              value: item.progress > 0 ? item.progress : null,
              backgroundColor: AppColors.surfaceElevated,
              valueColor: const AlwaysStoppedAnimation<Color>(AppColors.accent),
              minHeight: 4.0,
            ),
            const SizedBox(height: 3),
            Text('${(item.progress * 100).toInt()}%', style: AppTypography.label),
          ],
        );
      case MediaStatus.completed:
        return Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            BadgePill.status(text: 'Completed', color: AppColors.success),
            const Spacer(),
            if (item.outputPath != null) ...[
              IconButton(
                icon: const Icon(Icons.folder_open_rounded, size: 16),
                tooltip: 'Reveal in Explorer',
                padding: EdgeInsets.zero,
                constraints: const BoxConstraints(),
                color: AppColors.textSecondary,
                onPressed: () => FileUtils.revealFile(item.outputPath!),
              ),
              const SizedBox(width: 6),
              IconButton(
                icon: const Icon(Icons.play_circle_outline, size: 16),
                tooltip: 'Play Video',
                padding: EdgeInsets.zero,
                constraints: const BoxConstraints(),
                color: AppColors.accent,
                onPressed: () => FileUtils.openFile(item.outputPath!),
              ),
            ],
          ],
        );
      case MediaStatus.skipped:
        return BadgePill.status(text: 'Skipped', color: AppColors.warning);
      case MediaStatus.failed:
        return BadgePill.status(text: 'Failed', color: AppColors.error);
    }
  }
}
