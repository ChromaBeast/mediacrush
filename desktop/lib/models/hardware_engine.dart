/// Represents the detected hardware acceleration engine and silicon block.
class HardwareEngine {
  final String name;
  final String description;
  final String vendor;
  final String codec;
  final int typicalFps;
  final bool isHardware;

  const HardwareEngine({
    required this.name,
    required this.description,
    required this.vendor,
    required this.codec,
    required this.typicalFps,
    this.isHardware = true,
  });

  factory HardwareEngine.fallback() {
    return const HardwareEngine(
      name: 'libx265',
      description: 'Multi-Core CPU Software Encoder',
      vendor: 'CPU',
      codec: 'HEVC',
      typicalFps: 22,
      isHardware: false,
    );
  }

  factory HardwareEngine.fromCliName(String name) {
    switch (name.toLowerCase()) {
      case 'hevc_nvenc':
      case 'nvenc':
        return const HardwareEngine(
          name: 'hevc_nvenc',
          description: 'NVIDIA NVENC (CUDA)',
          vendor: 'NVIDIA',
          codec: 'HEVC',
          typicalFps: 240,
        );
      case 'av1_nvenc':
        return const HardwareEngine(
          name: 'av1_nvenc',
          description: 'NVIDIA NVENC (Ada/Blackwell)',
          vendor: 'NVIDIA',
          codec: 'AV1',
          typicalFps: 210,
        );
      case 'hevc_videotoolbox':
      case 'videotoolbox':
        return const HardwareEngine(
          name: 'hevc_videotoolbox',
          description: 'Apple Silicon VideoToolbox',
          vendor: 'Apple',
          codec: 'HEVC',
          typicalFps: 220,
        );
      case 'hevc_amf':
      case 'amf':
        return const HardwareEngine(
          name: 'hevc_amf',
          description: 'AMD AMF Engine',
          vendor: 'AMD',
          codec: 'HEVC',
          typicalFps: 180,
        );
      case 'hevc_qsv':
      case 'qsv':
        return const HardwareEngine(
          name: 'hevc_qsv',
          description: 'Intel Quick Sync Video',
          vendor: 'Intel',
          codec: 'HEVC',
          typicalFps: 190,
        );
      case 'hevc_vaapi':
      case 'vaapi':
        return const HardwareEngine(
          name: 'hevc_vaapi',
          description: 'Linux VA-API Hardware Layer',
          vendor: 'Linux/Mesa',
          codec: 'HEVC',
          typicalFps: 170,
        );
      default:
        return HardwareEngine.fallback();
    }
  }
}
