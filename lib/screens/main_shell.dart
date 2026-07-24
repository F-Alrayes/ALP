import 'package:flutter/material.dart';
import '../data/sample_data.dart';
import '../theme/app_theme.dart';
import 'announcement_screen.dart';
import 'home_screen.dart';
import 'more_screen.dart';
import 'news_screen.dart';

/// The app shell: an [IndexedStack] of top-level sections with a bottom
/// [NavigationBar]. Each tab keeps its own state while hidden.
class MainShell extends StatefulWidget {
  const MainShell({super.key});

  @override
  State<MainShell> createState() => _MainShellState();
}

class _MainShellState extends State<MainShell> {
  int _index = 0;

  late final List<Widget> _tabs = [
    const HomeScreen(),
    AnnouncementScreen(
      title: 'زواجات',
      icon: Icons.diamond_rounded,
      items: SampleData.marriages,
      detailTitle: 'زواج',
      emptyMessage: 'لا توجد مناسبات زواج',
    ),
    AnnouncementScreen(
      title: 'تعازي',
      icon: Icons.local_florist_rounded,
      items: SampleData.condolences,
      detailTitle: 'تعزية',
      emptyMessage: 'لا توجد تعازي',
    ),
    AnnouncementScreen(
      title: 'مناسبات',
      icon: Icons.celebration_rounded,
      items: SampleData.occasions,
      detailTitle: 'مناسبة',
      emptyMessage: 'لا توجد مناسبات',
    ),
    const NewsScreen(),
    const MoreScreen(),
  ];

  static const _destinations = [
    (Icons.home_rounded, 'الرئيسية'),
    (Icons.diamond_rounded, 'زواجات'),
    (Icons.local_florist_rounded, 'تعازي'),
    (Icons.celebration_rounded, 'مناسبات'),
    (Icons.campaign_rounded, 'الأخبار'),
    (Icons.grid_view_rounded, 'المزيد'),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(index: _index, children: _tabs),
      bottomNavigationBar: NavigationBarTheme(
        data: NavigationBarThemeData(
          backgroundColor: AppColors.surface,
          indicatorColor: AppColors.sage.withValues(alpha: 0.22),
          labelTextStyle: WidgetStateProperty.resolveWith(
            (states) => TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w600,
              color: states.contains(WidgetState.selected)
                  ? AppColors.primary
                  : AppColors.textSecondary,
            ),
          ),
          iconTheme: WidgetStateProperty.resolveWith(
            (states) => IconThemeData(
              size: 24,
              color: states.contains(WidgetState.selected)
                  ? AppColors.primary
                  : AppColors.textSecondary,
            ),
          ),
        ),
        child: NavigationBar(
          height: 68,
          selectedIndex: _index,
          onDestinationSelected: (i) => setState(() => _index = i),
          labelBehavior: NavigationDestinationLabelBehavior.alwaysShow,
          destinations: [
            for (final d in _destinations)
              NavigationDestination(icon: Icon(d.$1), label: d.$2),
          ],
        ),
      ),
    );
  }
}
