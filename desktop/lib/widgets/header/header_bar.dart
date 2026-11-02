import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../state/app_state.dart';
import '../../theme/app_colors.dart';
import '../../theme/app_typography.dart';
import '../common/app_logo.dart';
import '../common/update_dialog.dart';
import 'hardware_telemetry_hud.dart';

/// Top bar with window branding, directory selector, preset picker, and silicon HUD.
class HeaderBar extends StatelessWidget {
  const HeaderBar({super.key});

  Future<void> _pickDirectory(BuildContext context) async {
    final state = context.read<AppState>();
    final path = await FilePicker.getDirectoryPath(
      dialogTitle: 'Select Movie or TV Folder to Optimize',
    );
    if (path != null) {
      state.scanFolder(path);
    }
  }

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 20.0, vertical: 14.0),
      decoration: BoxDecoration(
        color: AppColors.background,
        border: Border(bottom: BorderSide(color: AppColors.border)),
      ),
      child: Row(
        children: [
          const AppLogo(size: 22.0),
          const SizedBox(width: 10.0),
          Text('MediaCrush', style: AppTypography.title),
          const SizedBox(width: 24.0),
          OutlinedButton.icon(
            onPressed: state.isScanning || state.isCompressing ? null : () => _pickDirectory(context),
            icon: const Icon(Icons.folder_open_outlined, size: 16),
            label: Text(
              state.selectedFolder != null ? 'Change Folder' : 'Select Folder',
              style: AppTypography.bodySecondary,
            ),
            style: OutlinedButton.styleFrom(
              foregroundColor: AppColors.textPrimary,
              side: BorderSide(color: AppColors.border),
              padding: const EdgeInsets.symmetric(horizontal: 14.0, vertical: 10.0),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6.0)),
            ),
          ),
          const SizedBox(width: 16.0),
          Text('Preset:', style: AppTypography.label),
          const SizedBox(width: 8.0),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10.0),
            decoration: BoxDecoration(
              color: AppColors.surface,
              borderRadius: BorderRadius.circular(6.0),
              border: Border.all(color: AppColors.border),
            ),
            child: DropdownButtonHideUnderline(
              child: DropdownButton<String>(
                value: state.preset,
                dropdownColor: AppColors.surfaceElevated,
                style: AppTypography.bodySecondary,
                items: const [
                  DropdownMenuItem(value: 'auto', child: Text('Auto Detect')),
                  DropdownMenuItem(value: 'anime', child: Text('Anime / 2D')),
                  DropdownMenuItem(value: 'film', child: Text('Live-Action Film')),
                  DropdownMenuItem(value: 'saver', child: Text('Ultra Saver')),
                ],
                onChanged: state.isCompressing ? null : (val) => val != null ? state.setPreset(val) : null,
              ),
            ),
          ),
          const Spacer(),
          if (state.availableUpdate != null) ...[
            TextButton.icon(
              onPressed: () => UpdateDialog.show(context, state.availableUpdate!, state.updateService),
              icon: const Icon(Icons.arrow_circle_up_rounded, color: AppColors.accent, size: 16),
              label: Text(
                'v${state.availableUpdate!.latestVersion} Available',
                style: AppTypography.monoBadge.copyWith(color: AppColors.accent, fontWeight: FontWeight.bold),
              ),
              style: TextButton.styleFrom(
                backgroundColor: AppColors.accent.withValues(alpha: 0.12),
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6)),
              ),
            ),
            const SizedBox(width: 12.0),
          ],
          HardwareTelemetryHud(engine: state.hardware),
        ],
      ),
    );
  }
}
