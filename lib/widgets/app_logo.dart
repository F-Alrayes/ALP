import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

/// The آل ريس wordmark.
///
/// This is a typographic placeholder that mirrors the reference logo — a fort
/// crown motif above the family name "آلريس" with "بن درع" beneath. Swap in the
/// official artwork by dropping an asset and using [AppLogo.image].
class AppLogo extends StatelessWidget {
  const AppLogo({super.key, this.size = 88, this.color = AppColors.primary});

  final double size;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(Icons.castle_rounded, size: size * 0.55, color: color),
        SizedBox(height: size * 0.04),
        Text(
          'آلريس',
          style: TextStyle(
            fontSize: size * 0.42,
            fontWeight: FontWeight.w900,
            color: color,
            height: 1.0,
          ),
        ),
        Text(
          'بـن درع',
          style: TextStyle(
            fontSize: size * 0.16,
            fontWeight: FontWeight.w600,
            color: color,
            letterSpacing: 2,
          ),
        ),
      ],
    );
  }
}

/// A compact, horizontal version of the logo for app bars.
class AppLogoMark extends StatelessWidget {
  const AppLogoMark({super.key, this.color = AppColors.primary, this.size = 28});

  final Color color;
  final double size;

  @override
  Widget build(BuildContext context) {
    return Icon(Icons.castle_rounded, size: size, color: color);
  }
}
