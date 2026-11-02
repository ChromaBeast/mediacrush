import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../state/app_state.dart';
import '../../theme/app_colors.dart';
import '../../theme/app_typography.dart';

/// Clean secondary bar clearly presenting input source and output destination path.
class DestinationBar extends StatelessWidget {
  const DestinationBar({super.key});

  Future<void> _pickFolder(BuildContext context) async {
    final state = context.read<AppState>();
    final path = await FilePicker.getDirectoryPath(dialogTitle: 'Select Video Folder');
    if (path != null) state.scanFolder(path);
  }

  Future<void> _pickFiles(BuildContext context) async {
    final state = context.read<AppState>();
    final files = await FilePicker.pickFiles(
      dialogTitle: 'Select Videos to Compress',
      type: FileType.video,
    );
    if (files.isNotEmpty) {
      final paths = files.map((f) => f.path).whereType<String>().toList();
      state.addFiles(paths);
    }
  }

  Future<void> _changeOutputFolder(BuildContext context) async {
    final state = context.read<AppState>();
    final path = await FilePicker.getDirectoryPath(dialogTitle: 'Select Output / Destination Folder');
    if (path != null) state.setOutputFolder(path);
  }

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 20.0, vertical: 10.0),
      decoration: BoxDecoration(
        color: AppColors.surface,
        border: Border(bottom: BorderSide(color: AppColors.border)),
      ),
      child: Row(
        children: [
          // Input Actions
          OutlinedButton.icon(
            onPressed: state.isCompressing ? null : () => _pickFolder(context),
            icon: const Icon(Icons.folder_open, size: 15),
            label: const Text('Add Folder'),
            style: OutlinedButton.styleFrom(
              foregroundColor: AppColors.textPrimary,
              side: BorderSide(color: AppColors.border),
              padding: const EdgeInsets.symmetric(horizontal: 12.0, vertical: 8.0),
              textStyle: AppTypography.bodySecondary,
            ),
          ),
          const SizedBox(width: 8.0),
          OutlinedButton.icon(
            onPressed: state.isCompressing ? null : () => _pickFiles(context),
            icon: const Icon(Icons.video_file_outlined, size: 15),
            label: const Text('Add Videos'),
            style: OutlinedButton.styleFrom(
              foregroundColor: AppColors.textPrimary,
              side: BorderSide(color: AppColors.border),
              padding: const EdgeInsets.symmetric(horizontal: 12.0, vertical: 8.0),
              textStyle: AppTypography.bodySecondary,
            ),
          ),
          const SizedBox(width: 16.0),
          // Output Destination Path (Clear & Prominent)
          Expanded(
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 10.0, vertical: 6.0),
              decoration: BoxDecoration(
                color: AppColors.surfaceElevated,
                borderRadius: BorderRadius.circular(6.0),
                border: Border.all(color: AppColors.border),
              ),
              child: Row(
                children: [
                  const Icon(Icons.output_rounded, size: 15, color: AppColors.accent),
                  const SizedBox(width: 8.0),
                  Text('Output: ', style: AppTypography.label.copyWith(color: AppColors.textPrimary)),
                  Expanded(
                    child: Text(
                      state.outputFolder ?? (state.selectedFolder != null ? '${state.selectedFolder}/crushed' : 'Not set (defaults to <source>/crushed)'),
                      style: AppTypography.bodySecondary.copyWith(
                        color: state.outputFolder != null ? AppColors.accent : AppColors.textMuted,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                  const SizedBox(width: 8.0),
                  InkWell(
                    onTap: state.isCompressing ? null : () => _changeOutputFolder(context),
                    borderRadius: BorderRadius.circular(4.0),
                    child: Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 6.0, vertical: 2.0),
                      child: Text('Change', style: AppTypography.label.copyWith(color: AppColors.accent)),
                    ),
                  ),
                  if (state.outputFolder != null) ...[
                    const SizedBox(width: 6.0),
                    IconButton(
                      icon: const Icon(Icons.folder_shared_outlined, size: 16),
                      tooltip: 'Open Output Folder',
                      padding: EdgeInsets.zero,
                      constraints: const BoxConstraints(),
                      color: AppColors.textSecondary,
                      onPressed: () => state.openOutputFolder(),
                    ),
                  ],
                ],
              ),
            ),
          ),
          if (state.items.isNotEmpty) ...[
            const SizedBox(width: 12.0),
            IconButton(
              icon: const Icon(Icons.delete_sweep_outlined, size: 18),
              tooltip: 'Clear List',
              color: AppColors.textMuted,
              onPressed: state.isCompressing ? null : () => state.clearItems(),
            ),
          ],
        ],
      ),
    );
  }
}
