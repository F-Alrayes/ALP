import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

/// Central design system for the آل ناصر (Al Nasser) family app.
///
/// Colours are sampled from the reference designs: a deep forest green paired
/// with a soft sage background and warm beige accents.
class AppColors {
  AppColors._();

  /// Primary deep forest green used for the logo, headings and icons.
  static const Color primary = Color(0xFF2E5A3B);

  /// A darker shade for pressed states and strong emphasis.
  static const Color primaryDark = Color(0xFF244A30);

  /// Muted sage green used for the login button and secondary chrome.
  static const Color sage = Color(0xFF7E9683);

  /// App background — a soft mint/sage off-white.
  static const Color background = Color(0xFFE7ECE5);

  /// Card surface.
  static const Color surface = Color(0xFFFFFFFF);

  /// A slightly recessed surface (unread news rows, search fields).
  static const Color surfaceMuted = Color(0xFFF1F3EF);

  /// Warm beige used behind imagery in the library cards.
  static const Color beige = Color(0xFFC7C1B0);

  /// Primary text colour (dark green).
  static const Color textPrimary = Color(0xFF2E5A3B);

  /// Secondary/body text.
  static const Color textSecondary = Color(0xFF6B7A6E);

  /// Divider / hairline.
  static const Color divider = Color(0xFFD6DCD3);
}

class AppTheme {
  AppTheme._();

  static ThemeData light() {
    final base = ThemeData.light(useMaterial3: true);
    final textTheme = GoogleFonts.tajawalTextTheme(base.textTheme).apply(
      bodyColor: AppColors.textPrimary,
      displayColor: AppColors.textPrimary,
    );

    return base.copyWith(
      scaffoldBackgroundColor: AppColors.background,
      colorScheme: base.colorScheme.copyWith(
        primary: AppColors.primary,
        secondary: AppColors.sage,
        surface: AppColors.surface,
      ),
      textTheme: textTheme,
      appBarTheme: AppBarTheme(
        backgroundColor: AppColors.background,
        surfaceTintColor: Colors.transparent,
        elevation: 0,
        centerTitle: false,
        iconTheme: const IconThemeData(color: AppColors.primary),
        titleTextStyle: GoogleFonts.tajawal(
          color: AppColors.primary,
          fontSize: 22,
          fontWeight: FontWeight.w700,
        ),
      ),
      cardTheme: CardThemeData(
        color: AppColors.surface,
        elevation: 0,
        shadowColor: Colors.black.withValues(alpha: 0.06),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(18),
        ),
      ),
      iconTheme: const IconThemeData(color: AppColors.primary),
    );
  }

  /// Soft shadow used across cards to match the elevated look in the designs.
  static List<BoxShadow> get cardShadow => [
        BoxShadow(
          color: Colors.black.withValues(alpha: 0.06),
          blurRadius: 16,
          offset: const Offset(0, 6),
        ),
      ];
}
