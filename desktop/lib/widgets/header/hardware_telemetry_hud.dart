import 'dart:io';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../models/hardware_engine.dart';
import '../../state/app_state.dart';
import '../../theme/app_colors.dart';
import '../../theme/app_typography.dart';

/// Interactive hardware acceleration chip with encoder switcher.
class HardwareTelemetryHud extends StatelessWidget {
  final HardwareEngine engine;

  const HardwareTelemetryHud({
    super.key,
    required this.engine,
  });

  @override
  Widget build(BuildContext context) {
    final state = context.read<AppState>();

    return PopupMenuButton<String>(
      tooltip: 'Change Hardware Encoder',
      color: AppColors.surfaceElevated,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8.0),
        side: BorderSide(color: AppColors.border),
      ),
      onSelected: (val) {
        if (val == 'redetect') {
          state.redetectHardware();
        } else {
          state.setHardware(HardwareEngine.fromCliName(val));
        }
      },
      itemBuilder: (_) => [
        if (Platform.isWindows || Platform.isLinux)
          const PopupMenuItem(
            value: 'hevc_nvenc',
            child: Text('NVIDIA NVENC (CUDA / RTX)', style: TextStyle(color: AppColors.textPrimary)),
          ),
        if (Platform.isWindows)
          const PopupMenuItem(
            value: 'hevc_amf',
            child: Text('AMD AMF Engine', style: TextStyle(color: AppColors.textPrimary)),
          ),
        if (Platform.isWindows || Platform.isLinux)
          const PopupMenuItem(
            value: 'hevc_qsv',
            child: Text('Intel QuickSync Video', style: TextStyle(color: AppColors.textPrimary)),
          ),
        if (Platform.isMacOS)
          const PopupMenuItem(
            value: 'hevc_videotoolbox',
            child: Text('Apple Silicon VideoToolbox', style: TextStyle(color: AppColors.textPrimary)),
          ),
        const PopupMenuItem(
          value: 'libx265',
          child: Text('Multi-Core CPU Software Encoder', style: TextStyle(color: AppColors.textSecondary)),
        ),
        const PopupMenuDivider(),
        const PopupMenuItem(
          value: 'redetect',
          child: Row(
            children: [
              Icon(Icons.refresh_rounded, size: 16, color: AppColors.accent),
              SizedBox(width: 8.0),
              Text('Re-scan Hardware', style: TextStyle(color: AppColors.accent)),
            ],
          ),
        ),
      ],
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10.0, vertical: 5.0),
        decoration: BoxDecoration(
          color: AppColors.surfaceElevated,
          borderRadius: BorderRadius.circular(6.0),
          border: Border.all(
            color: engine.isHardware ? AppColors.accent.withValues(alpha: 0.3) : AppColors.border,
            width: 1.0,
          ),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 7.0,
              height: 7.0,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: engine.isHardware ? AppColors.accent : AppColors.textMuted,
                boxShadow: engine.isHardware
                    ? [
                        BoxShadow(
                          color: AppColors.accent.withValues(alpha: 0.4),
                          blurRadius: 4.0,
                          spreadRadius: 1.0,
                        )
                      ]
                    : null,
              ),
            ),
            const SizedBox(width: 8.0),
            Text(
              engine.description,
              style: AppTypography.label.copyWith(
                color: AppColors.textPrimary,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(width: 6.0),
            const Icon(Icons.arrow_drop_down, size: 16, color: AppColors.textMuted),
          ],
        ),
      ),
    );
  }
}
