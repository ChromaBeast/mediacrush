import 'package:flutter/material.dart';
import '../../models/hardware_engine.dart';
import '../../theme/app_colors.dart';
import '../../theme/app_typography.dart';

/// The Signature Moment: Silicon hardware telemetry badge.
/// Presents authentic hardware encoding capabilities with quiet precision.
class HardwareTelemetryHud extends StatelessWidget {
  final HardwareEngine engine;

  const HardwareTelemetryHud({
    super.key,
    required this.engine,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
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
          const SizedBox(width: 8.0),
          Text(
            '•  ${engine.typicalFps} FPS',
            style: AppTypography.monoBadge.copyWith(
              color: engine.isHardware ? AppColors.accent : AppColors.textMuted,
            ),
          ),
        ],
      ),
    );
  }
}
