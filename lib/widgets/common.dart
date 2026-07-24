import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import 'app_logo.dart';

/// A rounded home button used on secondary screens (top-right of the designs,
/// which maps to the leading edge in an RTL layout).
class HomeButton extends StatelessWidget {
  const HomeButton({super.key, this.onTap});

  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: AppColors.surface,
      borderRadius: BorderRadius.circular(14),
      child: InkWell(
        borderRadius: BorderRadius.circular(14),
        onTap: onTap ?? () => Navigator.of(context).maybePop(),
        child: Container(
          width: 48,
          height: 48,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: AppColors.divider),
          ),
          child: const Icon(Icons.home_rounded, color: AppColors.primary),
        ),
      ),
    );
  }
}

/// Standard secondary-screen header: a title with the logo mark on the trailing
/// side and a home button on the leading side.
class ScreenHeader extends StatelessWidget {
  const ScreenHeader({
    super.key,
    required this.title,
    this.icon,
    this.showHomeButton = true,
  });

  final String title;
  final IconData? icon;

  /// Whether to show the home button. Hidden when the screen is a bottom-nav
  /// tab root (there is nothing to pop back to).
  final bool showHomeButton;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 8, 20, 8),
      child: Row(
        children: [
          // Title + logo mark sit at the start (top-right under RTL); the home
          // button sits at the end (top-left).
          Icon(icon ?? Icons.castle_rounded, color: AppColors.primary, size: 30),
          const SizedBox(width: 10),
          Flexible(
            child: Text(
              title,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.w700,
                color: AppColors.primary,
              ),
            ),
          ),
          const Spacer(),
          if (showHomeButton) const HomeButton(),
        ],
      ),
    );
  }
}

/// A rounded search field matching the design.
class SearchField extends StatelessWidget {
  const SearchField({
    super.key,
    this.hintText = 'ابحث',
    this.onChanged,
    this.controller,
  });

  final String hintText;
  final ValueChanged<String>? onChanged;
  final TextEditingController? controller;

  @override
  Widget build(BuildContext context) {
    return TextField(
      controller: controller,
      onChanged: onChanged,
      textAlign: TextAlign.right,
      decoration: InputDecoration(
        hintText: hintText,
        hintStyle: const TextStyle(color: AppColors.textSecondary),
        filled: true,
        fillColor: AppColors.surfaceMuted,
        contentPadding:
            const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: const BorderSide(color: AppColors.divider),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: const BorderSide(color: AppColors.primary, width: 1.5),
        ),
        suffixIcon: const Icon(Icons.search, color: AppColors.primary),
      ),
    );
  }
}

/// A small pill toggle used for the two-tab controls (News, Figures).
class SegmentTabs extends StatelessWidget {
  const SegmentTabs({
    super.key,
    required this.labels,
    required this.selectedIndex,
    required this.onChanged,
  });

  final List<String> labels;
  final int selectedIndex;
  final ValueChanged<int> onChanged;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Row(
          children: List.generate(labels.length, (i) {
            final selected = i == selectedIndex;
            return Expanded(
              child: GestureDetector(
                onTap: () => onChanged(i),
                behavior: HitTestBehavior.opaque,
                child: Padding(
                  padding: const EdgeInsets.symmetric(vertical: 12),
                  child: Text(
                    labels[i],
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      fontSize: 17,
                      fontWeight:
                          selected ? FontWeight.w700 : FontWeight.w500,
                      color: selected
                          ? AppColors.primary
                          : AppColors.textSecondary,
                    ),
                  ),
                ),
              ),
            );
          }),
        ),
        Stack(
          children: [
            Container(height: 2, color: AppColors.divider),
            AnimatedAlign(
              duration: const Duration(milliseconds: 200),
              curve: Curves.easeOut,
              alignment: Alignment(
                _alignmentX(selectedIndex, labels.length),
                0,
              ),
              child: FractionallySizedBox(
                widthFactor: 1 / labels.length,
                child: Container(height: 2.5, color: AppColors.primary),
              ),
            ),
          ],
        ),
      ],
    );
  }

  // Maps a tab index to an [Alignment] x value in the range [-1, 1].
  double _alignmentX(int index, int count) {
    if (count <= 1) return 0;
    return -1 + (2 * index / (count - 1));
  }
}

/// Placeholder circular avatar used when a figure has no photo.
class PlaceholderAvatar extends StatelessWidget {
  const PlaceholderAvatar({super.key, this.radius = 48});

  final double radius;

  @override
  Widget build(BuildContext context) {
    return CircleAvatar(
      radius: radius,
      backgroundColor: AppColors.background,
      child: Icon(
        Icons.person_outline_rounded,
        size: radius,
        color: AppColors.primary,
      ),
    );
  }
}

/// Small helper to show a "coming soon" sheet for not-yet-built actions.
void showComingSoon(BuildContext context, String feature) {
  ScaffoldMessenger.of(context)
    ..hideCurrentSnackBar()
    ..showSnackBar(
      SnackBar(
        behavior: SnackBarBehavior.floating,
        backgroundColor: AppColors.primary,
        content: Text('$feature — قريبًا', textAlign: TextAlign.right),
      ),
    );
}

/// Re-export for convenience.
class Logo extends AppLogo {
  const Logo({super.key, super.size, super.color});
}
