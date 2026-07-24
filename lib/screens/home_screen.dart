import 'package:flutter/material.dart';
import '../data/sample_data.dart';
import '../theme/app_theme.dart';
import '../widgets/app_logo.dart';
import 'library_screen.dart';
import 'news_screen.dart';
import 'figures_screen.dart';
import 'lineage_screen.dart';

/// The landing screen: logo, weather, and a grid of section shortcuts.
class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final latestNews = SampleData.news.first;

    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Top bar: weather (start/right) + info button (end/left) — the
              // logical order mirrors under RTL to match the design.
              Row(
                children: [
                  const _WeatherBadge(city: 'الرياض', temperature: 38),
                  const Spacer(),
                  _InfoButton(onTap: () => _showAbout(context)),
                ],
              ),
              const SizedBox(height: 8),
              const Center(child: AppLogo(size: 120)),
              const SizedBox(height: 28),

              // Row 1: News (start/right) + Library (end/left).
              IntrinsicHeight(
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Expanded(
                      child: _HomeCard(
                        title: 'الأخبار',
                        icon: Icons.article_rounded,
                        onTap: () => _open(context, const NewsScreen()),
                        child: _NewsPreview(title: latestNews.title),
                      ),
                    ),
                    const SizedBox(width: 14),
                    Expanded(
                      child: _HomeCard(
                        title: 'المكتبة',
                        icon: Icons.menu_book_rounded,
                        onTap: () => _open(context, const LibraryScreen()),
                        child: const _LibraryWatermark(),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 14),

              // Row 2: Figures (start/right) + Lineage (end/left).
              IntrinsicHeight(
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Expanded(
                      child: _HomeCard(
                        title: 'الشخصيات',
                        icon: Icons.workspace_premium_rounded,
                        onTap: () => _open(context, const FiguresScreen()),
                        child: const Text(
                          'يمكنك الاطلاع على القائمة المليئة بالشخصيات التي كان '
                          'لها دور مهم.',
                          textAlign: TextAlign.right,
                          style: TextStyle(color: AppColors.textSecondary),
                        ),
                      ),
                    ),
                    const SizedBox(width: 14),
                    Expanded(
                      child: _HomeCard(
                        title: 'النسب',
                        icon: Icons.groups_rounded,
                        onTap: () => _open(context, const LineageScreen()),
                        child: const Text(
                          'هنا يمكننا ان نتعرف اكثر على عائلة آل ناصر وجذورها.',
                          textAlign: TextAlign.right,
                          style: TextStyle(color: AppColors.textSecondary),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 14),

              // Row 3: Connect (full width).
              IntrinsicHeight(
                child: _HomeCard(
                  title: 'تواصل',
                  icon: Icons.hub_rounded,
                  minHeight: 150,
                  onTap: () => _showConnect(context),
                  child: const Text(
                    'يمكنكم المشاركه في التطبيق من هنا.',
                    textAlign: TextAlign.right,
                    style: TextStyle(color: AppColors.textSecondary),
                  ),
                ),
              ),
              const SizedBox(height: 20),

              // Login button (end side — bottom-left under RTL).
              Align(
                alignment: AlignmentDirectional.centerEnd,
                child: _LoginButton(onTap: () => _showLogin(context)),
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _open(BuildContext context, Widget screen) {
    Navigator.of(context).push(MaterialPageRoute(builder: (_) => screen));
  }

  void _showAbout(BuildContext context) {
    showDialog<void>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('عن التطبيق', textAlign: TextAlign.right),
        content: const Text(
          'تطبيق أسرة آل ناصر — يجمع أخبار العائلة، مكتبتها، شخصياتها '
          'ونسبها في مكان واحد.',
          textAlign: TextAlign.right,
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('حسنًا'),
          ),
        ],
      ),
    );
  }

  void _showConnect(BuildContext context) {
    showModalBottomSheet<void>(
      context: context,
      backgroundColor: AppColors.surface,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (_) => const _ConnectSheet(),
    );
  }

  void _showLogin(BuildContext context) {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        behavior: SnackBarBehavior.floating,
        backgroundColor: AppColors.primary,
        content: Text('تسجيل الدخول — قريبًا', textAlign: TextAlign.right),
      ),
    );
  }
}

class _HomeCard extends StatelessWidget {
  const _HomeCard({
    required this.title,
    required this.icon,
    required this.child,
    this.onTap,
    this.minHeight = 160,
  });

  final String title;
  final IconData icon;
  final Widget child;
  final VoidCallback? onTap;
  final double minHeight;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: AppColors.surface,
      borderRadius: BorderRadius.circular(18),
      child: InkWell(
        borderRadius: BorderRadius.circular(18),
        onTap: onTap,
        child: Container(
          constraints: BoxConstraints(minHeight: minHeight),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(18),
            boxShadow: AppTheme.cardShadow,
          ),
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Icon leads (rightmost under RTL) with the title beside it,
              // pinned to the start/right edge as in the design.
              Row(
                mainAxisAlignment: MainAxisAlignment.start,
                children: [
                  Icon(icon, color: AppColors.primary, size: 24),
                  const SizedBox(width: 8),
                  Flexible(
                    child: Text(
                      title,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        fontSize: 19,
                        fontWeight: FontWeight.w700,
                        color: AppColors.primary,
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              Expanded(child: child),
            ],
          ),
        ),
      ),
    );
  }
}

class _NewsPreview extends StatelessWidget {
  const _NewsPreview({required this.title});
  final String title;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      mainAxisAlignment: MainAxisAlignment.end,
      children: [
        const Divider(color: AppColors.divider),
        const Align(
          alignment: Alignment.centerLeft,
          child: Icon(Icons.campaign_rounded, color: AppColors.primary),
        ),
        const SizedBox(height: 8),
        Text(
          title,
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
          textAlign: TextAlign.right,
          style: const TextStyle(
            color: AppColors.textSecondary,
            fontWeight: FontWeight.w600,
          ),
        ),
      ],
    );
  }
}

class _LibraryWatermark extends StatelessWidget {
  const _LibraryWatermark();

  @override
  Widget build(BuildContext context) {
    return const Align(
      alignment: Alignment.bottomLeft,
      child: Icon(
        Icons.menu_book_rounded,
        size: 64,
        color: AppColors.divider,
      ),
    );
  }
}

class _WeatherBadge extends StatelessWidget {
  const _WeatherBadge({required this.city, required this.temperature});
  final String city;
  final int temperature;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.end,
      children: [
        Text(
          '$temperature°',
          style: const TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.w700,
            color: AppColors.primary,
          ),
        ),
        Text(
          city,
          style: const TextStyle(
            fontSize: 15,
            fontWeight: FontWeight.w600,
            color: AppColors.primary,
          ),
        ),
      ],
    );
  }
}

class _InfoButton extends StatelessWidget {
  const _InfoButton({this.onTap});
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: AppColors.surface,
      borderRadius: BorderRadius.circular(12),
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: onTap,
        child: Container(
          width: 44,
          height: 44,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: AppColors.divider),
          ),
          child: const Icon(Icons.info_outline_rounded,
              color: AppColors.primary, size: 22),
        ),
      ),
    );
  }
}

class _LoginButton extends StatelessWidget {
  const _LoginButton({this.onTap});
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: AppColors.sage,
      borderRadius: BorderRadius.circular(16),
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: onTap,
        child: Container(
          width: 150,
          height: 96,
          padding: const EdgeInsets.all(16),
          child: const Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Icon(Icons.login_rounded, color: Colors.white, size: 26),
              Text(
                'دخول',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 20,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _ConnectSheet extends StatelessWidget {
  const _ConnectSheet();

  @override
  Widget build(BuildContext context) {
    final items = [
      (Icons.person_add_alt_1_rounded, 'إضافة فرد من العائلة'),
      (Icons.photo_camera_back_rounded, 'مشاركة صورة'),
      (Icons.campaign_rounded, 'إرسال خبر'),
      (Icons.support_agent_rounded, 'التواصل مع اللجنة'),
    ];
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(16, 20, 16, 20),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text(
              'تواصل ومشاركة',
              textAlign: TextAlign.right,
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.w700,
                color: AppColors.primary,
              ),
            ),
            const SizedBox(height: 12),
            for (final item in items)
              ListTile(
                trailing: Icon(item.$1, color: AppColors.primary),
                title: Text(item.$2, textAlign: TextAlign.right),
                onTap: () => Navigator.of(context).pop(),
              ),
          ],
        ),
      ),
    );
  }
}
